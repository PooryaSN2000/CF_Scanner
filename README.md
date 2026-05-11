```text
[*] Parsing IP ranges from export.ipv4...
[*] Total IPs to test: 2840
[*] Testing TCP Port 443 (Threads: 100)...
[*] Goal: Find 10 working VLESS IPs.

[+] Found working IP: 104.18.2.14     | Latency: 112ms  (1/10)
[+] Found working IP: 172.64.19.2     | Latency: 85ms   (2/10)
...
[*] Target reached! Cancelling remaining checks...

========================================
      FINAL VLESS IPS (FASTEST FIRST)      
========================================
172.64.19.2          -> 85ms
104.18.2.14          -> 112ms
...
========================================
[*] Saved 10 IPs to 'vless_working_ips.txt' (Ready to paste into V2ray)
Here is a clean, professional `README.md` file tailored for your GitHub repository. You can copy this directly into your GitHub project.

***
```markdown
# 🚀 V2ray VLESS IP Scanner

A fast, multithreaded Python script designed to find the lowest-latency working IP addresses from large CIDR lists (e.g., Cloudflare IP ranges) specifically for **V2ray VLESS** configurations.

Unlike standard ICMP ping tools, this script uses **TCP socket connections** on your specified port (default `443`). This perfectly mimics how V2ray establishes connections, ensuring that the IPs you find are not just online, but actually accessible through your ISP for VLESS traffic.

## ✨ Features
* **Extremely Fast:** Uses Python's `ThreadPoolExecutor` to test up to 100 IPs simultaneously.
* **TCP Port Checking:** Tests actual TCP connections on port 443 (or any custom port) to bypass false positives from ICMP/Ping blocks.
* **Memory Efficient:** Uses mathematical index sampling instead of loading massive subnets (like `/8`) into memory, preventing crashes.
* **Latency Sorting:** Measures connection handshake times and outputs the fastest IPs at the top of the list.
* **No Dependencies:** Built entirely with Python's standard library. No `pip install` required.

## 📋 Prerequisites
* Python 3.6 or higher.
* A text file containing IPv4 CIDR ranges (e.g., Cloudflare IP ranges). 

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME

```

2. **Prepare your IP list:**
Ensure you have a file named `export.ipv4` in the same directory. This file should contain IP subnets, one per line:
```text
3.25.205.0/24
5.226.179.0/24
...

```


3. **Run the script:**
```bash
python cf_scanner.py

```


4. **Get your results:**
Once the target number of working IPs is found, the script will stop and save the sorted list (fastest first) to `vless_working_ips.txt`. You can copy these directly into the `address` field of your V2ray client.

## ⚙️ Configuration

You can easily customize the script's behavior by editing the variables at the top of `cf_scanner.py`:

| Variable | Default | Description |
| --- | --- | --- |
| `FILE_NAME` | `'export.ipv4'` | The input file containing your CIDR ranges. |
| `OUTPUT_FILE` | `'vless_working_ips.txt'` | The file where the working, sorted IPs will be saved. |
| `TARGET_WORKING_IPS` | `10` | The script stops automatically once it finds this many working IPs. |
| `SAMPLES_PER_SUBNET` | `2` | How many random IPs to test from *each* subnet range. |
| `MAX_THREADS` | `100` | How many IPs to test concurrently. |
| `VLESS_PORT` | `443` | The target TCP port (443 is standard for TLS VLESS). |
| `TIMEOUT` | `1.5` | Max seconds to wait for a connection before considering the IP dead/blocked. |

## 🖥️ Example Output

```text
[*] Parsing IP ranges from export.ipv4...
[*] Total IPs to test: 2840
[*] Testing TCP Port 443 (Threads: 100)...
[*] Goal: Find 10 working VLESS IPs.

[+] Found working IP: 104.18.2.14     | Latency: 112ms  (1/10)
[+] Found working IP: 172.64.19.2     | Latency: 85ms   (2/10)
...
[*] Target reached! Cancelling remaining checks...

========================================
      FINAL VLESS IPS (FASTEST FIRST)      
========================================
172.64.19.2          -> 85ms
104.18.2.14          -> 112ms
...
========================================
[*] Saved 10 IPs to 'vless_working_ips.txt' (Ready to paste into V2ray)


```
