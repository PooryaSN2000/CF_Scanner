import ipaddress
import random
import concurrent.futures
import socket
import time
import sys

# --- Configuration ---
FILE_NAME = 'export.ipv4'
OUTPUT_FILE = 'working_ips.txt'
TARGET_WORKING_IPS = 10         
SAMPLES_PER_SUBNET = 2          
MAX_THREADS = 100               # Increased to 100 since TCP sockets are very lightweight
VLESS_PORT = 443                # The port your VLESS config uses (usually 443 for TLS)
TIMEOUT = 1.5                   # Max seconds to wait for a connection
# ---------------------

def get_random_ips(filename, samples_per_subnet):
    """Reads the file and mathematically extracts random IPs from each range."""
    ips_to_test = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    network = ipaddress.IPv4Network(line, strict=False)
                    num_hosts = network.num_addresses - 2 
                    
                    if num_hosts <= 0: continue
                        
                    sample_size = min(samples_per_subnet, num_hosts)
                    random_indices = random.sample(range(1, num_hosts + 1), sample_size)
                    
                    for idx in random_indices:
                        random_ip = network.network_address + idx
                        ips_to_test.append(str(random_ip))
                        
                except ValueError:
                    pass # Skip invalid lines silently
    except FileNotFoundError:
        print(f"[!] Error: Could not find {filename}")
        sys.exit(1)
        
    random.shuffle(ips_to_test)
    return ips_to_test

def tcp_ping(ip):
    """Attempts to establish a TCP connection to the IP on the specified port."""
    try:
        start_time = time.time()
        # Create a raw TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            # Try to connect to the IP on the VLESS port (443)
            s.connect((ip, VLESS_PORT))
            
            # If it connects, calculate how many milliseconds it took
            end_time = time.time()
            latency = int((end_time - start_time) * 1000)
            return (ip, latency)
            
    except (socket.timeout, ConnectionRefusedError, OSError):
        # Connection failed or timed out (IP is blocked or dead on this port)
        return None

def main():
    print(f"[*] Parsing IP ranges from {FILE_NAME}...")
    ips_to_test = get_random_ips(FILE_NAME, SAMPLES_PER_SUBNET)
    
    if not ips_to_test:
        print("[-] No valid IPs generated.")
        return

    print(f"[*] Total IPs to test: {len(ips_to_test)}")
    print(f"[*] Testing TCP Port {VLESS_PORT} (Threads: {MAX_THREADS})...")
    print(f"[*] Goal: Find {TARGET_WORKING_IPS} working VLESS IPs.\n")

    working_ips = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_ip = {executor.submit(tcp_ping, ip): ip for ip in ips_to_test}
        
        for future in concurrent.futures.as_completed(future_to_ip):
            result = future.result()
            if result:
                ip, latency = result
                working_ips.append((ip, latency))
                print(f"[+] Found working IP: {ip:<15} | Latency: {latency}ms  ({len(working_ips)}/{TARGET_WORKING_IPS})")
                
                if len(working_ips) >= TARGET_WORKING_IPS:
                    print("\n[*] Target reached! Cancelling remaining checks...")
                    for f in future_to_ip:
                        f.cancel()
                    break

    # Sort the working IPs by latency (fastest first)
    working_ips.sort(key=lambda x: x[1])

    print("\n" + "="*40)
    print("      FINAL VLESS IPS (FASTEST FIRST)      ")
    print("="*40)
    for ip, latency in working_ips:
        print(f"{ip:<20} -> {latency}ms")
    print("="*40)

    # Save sorted results to file
    if working_ips:
        try:
            with open(OUTPUT_FILE, 'w') as out_file:
                for ip, latency in working_ips:
                    out_file.write(f"{ip}\n")
            print(f"[*] Saved {len(working_ips)} IPs to '{OUTPUT_FILE}' (Ready to paste into V2ray)")
        except IOError as e:
            print(f"[!] Error saving to file: {e}")

if __name__ == '__main__':
    main()