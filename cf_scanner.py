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
import urllib.parse
import copy
import threading
import atexit

# --- Configuration ---
FILE_NAME = 'export.ipv4'
OUTPUT_FILE = 'working_ips.txt'
LINKS_FILE = 'vless_links.txt'       
CONFIG_TEMPLATE_FILE = 'config.json' 
XRAY_PATH = 'Xray-windows-64\\xray.exe' 
TARGET_WORKING_IPS = 5          # How many top/best IPs to save at the end
SAMPLES_PER_SUBNET = 2          
MAX_THREADS = 5                 
PING_TIMEOUT = 5.0              
SPEED_TIMEOUT = 15.0            
MAX_IPS_TO_TEST = 200           

# Testing Endpoints
PING_URL = "http://cp.cloudflare.com/"
SPEED_TEST_URL = "http://speed.cloudflare.com/__down?bytes=150000" 
BASE_PORT = 20000 
# ---------------------

print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg)

def clean_temp_files():
    for file in os.listdir('.'):
        if file.startswith('temp_') and file.endswith('.json'):
            try:
                os.remove(file)
            except Exception:
                pass

atexit.register(clean_temp_files)

def load_base_config():
    try:
        with open(CONFIG_TEMPLATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        safe_print(f"[!] FATAL: Could not load {CONFIG_TEMPLATE_FILE}: {e}")
        sys.exit(1)

def generate_test_config(base_config, ip, local_port):
    test_config = copy.deepcopy(base_config)
    if "dns" in test_config:
        del test_config["dns"]
        
    test_config["inbounds"] = [{
        "port": local_port,
        "listen": "127.0.0.1",
        "protocol": "http",
        "settings": {"timeout": 0}
    }]
    
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

def generate_vless_url(ip, latency, speed, base_config):
    try:
        outbound = next((out for out in base_config.get("outbounds", []) if out.get("protocol") == "vless"), base_config["outbounds"][0])
        vnext = outbound["settings"]["vnext"][0]
        uuid = vnext["users"][0]["id"]
        port = vnext["port"]
        
        stream = outbound.get("streamSettings", {})
        network = stream.get("network", "ws")
        security = stream.get("security", "tls")
        
        sni = stream.get("tlsSettings", {}).get("serverName", "") if security == "tls" else ""
        path = stream.get("wsSettings", {}).get("path", "") if network == "ws" else ""
        host = stream.get("wsSettings", {}).get("host", sni) if network == "ws" else ""
        
        query_params = ["encryption=none", f"security={security}", f"type={network}"]
        if sni: query_params.append(f"sni={urllib.parse.quote(sni)}")
        if host: query_params.append(f"host={urllib.parse.quote(host)}")
        if path: query_params.append(f"path={urllib.parse.quote(path, safe='')}")
        
        query_string = "&".join(query_params)
        remark = urllib.parse.quote(f"CF-{ip} ({latency}ms | {speed:.2f}Mbps)")
        
        return f"vless://{uuid}@{ip}:{port}?{query_string}#{remark}"
    except Exception as e:
        return f"# Error generating link for {ip}: {e}"

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
        safe_print(f"[!] Error: {filename} not found.")
        sys.exit(1)
        
    random.shuffle(ips_to_test)
    if MAX_IPS_TO_TEST > 0:
        return ips_to_test[:MAX_IPS_TO_TEST]
    return ips_to_test

def xray_test(ip, local_port, base_config, is_default=False):
    label = "[DEFAULT]" if is_default else "[SCAN]"
    config_path = f"temp_{local_port}.json"
    abs_config_path = os.path.abspath(config_path)
    
    config_data = generate_test_config(base_config, ip, local_port)
    with open(abs_config_path, "w") as f:
        json.dump(config_data, f)
        
    proc = None
    try:
        xray_dir = os.path.dirname(os.path.abspath(XRAY_PATH))
        proc = subprocess.Popen(
            [os.path.abspath(XRAY_PATH), "run", "-c", abs_config_path], 
            cwd=xray_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        time.sleep(1.0) 
        if proc.poll() is not None:
            safe_print(f"{label} {ip:<15} | Failed (Xray Crash)")
            return None
            
        proxy_handler = urllib.request.ProxyHandler({'http': f'http://127.0.0.1:{local_port}'})
        opener = urllib.request.build_opener(proxy_handler)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        # Test 1: Latency (Ping)
        start_ping = time.time()
        try:
            ping_req = urllib.request.Request(PING_URL, headers=headers)
            with opener.open(ping_req, timeout=PING_TIMEOUT) as r:
                if r.status not in [200, 204]:
                    safe_print(f"{label} {ip:<15} | Failed (Bad HTTP Status)")
                    return None
        except Exception:
            safe_print(f"{label} {ip:<15} | Failed (Timeout / No Ping)")
            return None
            
        latency = int((time.time() - start_ping) * 1000)

        # Test 2: Speed (Download)
        start_speed = time.time()
        try:
            speed_req = urllib.request.Request(SPEED_TEST_URL, headers=headers)
            with opener.open(speed_req, timeout=SPEED_TIMEOUT) as r:
                data = r.read()
                bytes_downloaded = len(data)
        except Exception:
            safe_print(f"{label} {ip:<15} | Ping: {latency:<4}ms | Failed (Speed Test Timeout)")
            return None
            
        time_taken = time.time() - start_speed
        speed_mbps = (bytes_downloaded * 8) / (time_taken * 1_000_000)

        safe_print(f"{label} {ip:<15} | Ping: {latency:<4}ms | Speed: {speed_mbps:.2f} Mbps [SUCCESS]")
        return (ip, latency, speed_mbps)
                
    finally:
        if proc:
            proc.terminate()
            try: proc.wait(timeout=1)
            except: proc.kill()
        if os.path.exists(abs_config_path):
            try: os.remove(abs_config_path)
            except: pass 

def main():
    clean_temp_files()
    
    if not os.path.exists(XRAY_PATH):
        safe_print(f"[!] FATAL: Xray not found at: {XRAY_PATH}")
        return
        
    base_config = load_base_config()
    
    safe_print("="*70)
    safe_print("STEP 1: Testing default config.json address...")
    default_ip = None
    for out in base_config.get("outbounds", []):
        if out.get("protocol") == "vless":
            default_ip = out["settings"]["vnext"][0]["address"]
            break
    if not default_ip:
        default_ip = base_config["outbounds"][0]["settings"]["vnext"][0]["address"]
        
    safe_print(f"[*] Default IP found: {default_ip}")
    default_result = xray_test(default_ip, BASE_PORT - 1, base_config, is_default=True)
    
    if default_result:
        safe_print("[V] Default config is WORKING. Proceeding to scan for more...")
    else:
        safe_print("[X] WARNING: Your default config failed! Check your UUID/SNI/Path.")
        choice = input("[?] Do you still want to continue scanning other IPs? (y/n): ")
        if choice.lower() != 'y':
            return
            
    safe_print("="*70 + "\n")
    ips_to_test = get_random_ips(FILE_NAME, SAMPLES_PER_SUBNET)
    total_ips = len(ips_to_test)
    safe_print(f"STEP 2: Testing all {total_ips} IPs to find the lowest ping...")
    
    working_ips = []
    checked = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(xray_test, ip, BASE_PORT + i, base_config): ip 
            for i, ip in enumerate(ips_to_test)
        }
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            checked += 1
            if result:
                working_ips.append(result)
                
            safe_print(f"--- Progress: {checked}/{total_ips} Checked | {len(working_ips)} Working IPs Found ---")

    # --- THE MAGIC CHANGE IS HERE ---
    # Sort all working IPs by Latency (Ascending), then Speed (Descending) as a tie-breaker
    working_ips.sort(key=lambda x: (x[1], -x[2]))
    
    # Keep only the top N best IPs
    if len(working_ips) > TARGET_WORKING_IPS:
        working_ips = working_ips[:TARGET_WORKING_IPS]
    
    safe_print("\n" + "="*70)
    safe_print(f"[*] Filtering complete. Here are the TOP {len(working_ips)} lowest ping connections:")
    safe_print(f"{'IP Address':<18} | {'Latency':<10} | {'Download Speed'}")
    safe_print("-" * 70)
    
    with open(OUTPUT_FILE, 'w') as f_ip, open(LINKS_FILE, 'w', encoding='utf-8') as f_links:
        for ip, lat, speed in working_ips:
            safe_print(f"{ip:<18} | {lat:<8}ms | {speed:.2f} Mbps")
            f_ip.write(f"{ip}\n")
            vless_url = generate_vless_url(ip, lat, speed, base_config)
            f_links.write(f"{vless_url}\n")
            
    safe_print("="*70)
    safe_print(f"[*] Done. Top {len(working_ips)} raw IPs saved to {OUTPUT_FILE}")
    safe_print(f"[*] Done. Top {len(working_ips)} VLESS configs sorted by ping saved to {LINKS_FILE}")

if __name__ == '__main__':
    main()