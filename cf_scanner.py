import ipaddress
import random
import concurrent.futures
import socket
import time
import sys
import subprocess
import json
import os
import urllib.request
import copy

# --- Configuration ---
FILE_NAME = 'export.ipv4'
OUTPUT_FILE = 'working_ips.txt'
CONFIG_TEMPLATE_FILE = 'config.json' 
XRAY_PATH = 'Xray-windows-64\\xray.exe' # Ensure this is correct

TARGET_WORKING_IPS = 5         
SAMPLES_PER_SUBNET = 2          
MAX_THREADS = 5                 
TIMEOUT = 5.0                   
TEST_URL = "http://cp.cloudflare.com/"
# ---------------------

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def load_base_config():
    try:
        with open(CONFIG_TEMPLATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] FATAL: Could not load {CONFIG_TEMPLATE_FILE}: {e}")
        sys.exit(1)

def generate_test_config(base_config, ip, local_port):
    test_config = copy.deepcopy(base_config)
    
    # --- FIX 1: Remove DNS to prevent geosite.dat / geoip.dat crashes ---
    if "dns" in test_config:
        del test_config["dns"]

    test_config["inbounds"] = [{
        "port": local_port,
        "listen": "127.0.0.1",
        "protocol": "http",
        "settings": {"timeout": 0}
    }]
    
    # Target the VLESS outbound
    found = False
    for outbound in test_config.get("outbounds", []):
        if outbound.get("protocol") == "vless":
            outbound["settings"]["vnext"][0]["address"] = ip
            found = True
            break
    if not found:
        test_config["outbounds"][0]["settings"]["vnext"][0]["address"] = ip

    test_config["routing"] = {
        "domainStrategy": "AsIs",
        "rules": [{"type": "field", "port": "0-65535", "outboundTag": test_config["outbounds"][0]["tag"]}]
    }
    return test_config

def get_random_ips(filename, samples_per_subnet):
    ips_to_test = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or "/" not in line: continue
                try:
                    network = ipaddress.IPv4Network(line, strict=False)
                    num_hosts = network.num_addresses - 2 
                    if num_hosts <= 0: continue
                    sample_size = min(samples_per_subnet, num_hosts)
                    random_indices = random.sample(range(1, num_hosts + 1), sample_size)
                    for idx in random_indices:
                        ips_to_test.append(str(network.network_address + idx))
                except ValueError: pass
    except FileNotFoundError:
        print(f"[!] Error: {filename} not found.")
        sys.exit(1)
    random.shuffle(ips_to_test)
    return ips_to_test[:100] # Change this back once it works

def xray_ping(ip, base_config, is_default=False):
    label = "[DEFAULT-CHECK]" if is_default else f"[SCAN]"
    local_port = get_free_port()
    config_path = f"temp_{local_port}.json"
    
    # --- FIX 2: Use absolute path for config so Xray can find it ---
    abs_config_path = os.path.abspath(config_path)
    
    config_data = generate_test_config(base_config, ip, local_port)
    
    with open(abs_config_path, "w") as f:
        json.dump(config_data, f)

    print(f"{label} {ip}: Starting Xray on port {local_port}...")
    
    proc = None
    try:
        # Get the directory where Xray is located
        xray_dir = os.path.dirname(os.path.abspath(XRAY_PATH))
        
        # --- FIX 3: Capture both STDOUT and STDERR to see the exact crash reason ---
        proc = subprocess.Popen(
            [os.path.abspath(XRAY_PATH), "run", "-c", abs_config_path], 
            cwd=xray_dir, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        time.sleep(1.0) 
        if proc.poll() is not None:
            stdout_logs, stderr_logs = proc.communicate()
            error_msg = stderr_logs.strip() or stdout_logs.strip() or "Unknown Error (Check Path or Permissions)"
            print(f"{label} {ip}: Xray crashed! Error:\n{error_msg}")
            return None

        start_time = time.time()
        proxy_handler = urllib.request.ProxyHandler({'http': f'http://127.0.0.1:{local_port}'})
        opener = urllib.request.build_opener(proxy_handler)
        
        with opener.open(TEST_URL, timeout=TIMEOUT) as r:
            if r.status in [200, 204]:
                latency = int((time.time() - start_time) * 1000)
                print(f"{label} {ip}: SUCCESS! Real Latency: {latency}ms")
                return (ip, latency)
                
    except Exception as e:
        print(f"{label} {ip}: Failed. ({type(e).__name__})")
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if os.path.exists(abs_config_path):
            try: os.remove(abs_config_path)
            except: pass

    return None

def main():
    if not os.path.exists(XRAY_PATH):
        print(f"[!] FATAL: Xray not found at: {XRAY_PATH}")
        return

    base_config = load_base_config()
    
    print("="*50)
    print("STEP 1: Testing your default config.json address...")
    try:
        # Attempt to find the default IP for the check
        found_ip = False
        for out in base_config.get("outbounds", []):
            if out.get("protocol") == "vless":
                default_ip = out["settings"]["vnext"][0]["address"]
                found_ip = True
                break
        
        if not found_ip:
            default_ip = base_config["outbounds"][0]["settings"]["vnext"][0]["address"]

        print(f"[*] Default IP found in config: {default_ip}")
        default_result = xray_ping(default_ip, base_config, is_default=True)
        
        if default_result:
            print("[V] Default config is WORKING. Proceeding to scan for more...")
        else:
            print("[X] WARNING: Your default config failed! Check your UUID/SNI/Path.")
            choice = input("[?] Do you still want to continue scanning other IPs? (y/n): ")
            if choice.lower() != 'y':
                return
    except Exception as e:
        print(f"[!] Could not parse default IP from config: {e}")
    print("="*50 + "\n")

    ips_to_test = get_random_ips(FILE_NAME, SAMPLES_PER_SUBNET)
    print(f"STEP 2: Testing {len(ips_to_test)} IPs from {FILE_NAME}...")

    working_ips = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(xray_ping, ip, base_config): ip for ip in ips_to_test}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                working_ips.append(result)
                if len(working_ips) >= TARGET_WORKING_IPS:
                    print("\n[*] Target IP count reached.")
                    break

    working_ips.sort(key=lambda x: x[1])
    
    print("\n" + "="*50)
    print(f"{'IP Address':<20} | {'Latency'}")
    print("-" * 50)
    with open(OUTPUT_FILE, 'w') as f:
        for ip, lat in working_ips:
            print(f"{ip:<20} | {lat}ms")
            f.write(f"{ip}\n")
    print("="*50)
    print(f"[*] Done. Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()