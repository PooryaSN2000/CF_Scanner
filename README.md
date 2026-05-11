---

# 🚀 Cloudflare IP Scanner

A lightning-fast, multithreaded Python script designed to hunt down the lowest-latency working IP addresses from large CIDR lists (e.g., Cloudflare IP ranges) specifically tailored for **V2ray VLESS** configurations.

Unlike standard ICMP ping tools, this script utilizes **TCP socket connections** on your specified port (default `443`). This perfectly mimics how V2ray establishes connections, guaranteeing that the IPs you find are not just online, but actively accepting VLESS traffic through your ISP.

---

## ✨ Features

* **⚡ Extremely Fast:** Leverages Python's `ThreadPoolExecutor` to test up to 100 IPs simultaneously.
* **🛡️ TCP Port Checking:** Tests actual TCP connections to bypass false positives and restrictive ICMP/Ping blocks.
* **🧠 Memory Efficient:** Utilizes mathematical index sampling instead of loading massive subnets (like `/8`) into RAM, preventing memory leaks and crashes.
* **⏱️ Latency Sorting:** Measures connection handshake times and automatically ranks the fastest IPs at the top.
* **📦 Zero Dependencies:** Built entirely with Python's standard library. No `pip install` required.

---

## 📋 Prerequisites

* Python 3.6 or higher installed on your system.
* A text file containing IPv4 CIDR ranges (e.g., `export.ipv4`).

---

## 🚀 Installation & Usage

### 1. Clone the repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

```

### 2. Prepare your IP list

Ensure you have a file named `export.ipv4` in the root directory of the script. This file should contain your target IP subnets, one per line:

```text
3.25.205.0/24
5.226.179.0/24
104.16.0.0/12

```

### 3. Run the scanner

```bash
python cf_scanner.py

```

### 4. Apply your results

Once the script reaches your target number of working IPs, it will stop and save the sorted list to `vless_working_ips.txt`. Copy these IPs directly into the `address` field of your V2ray client.

---

## ⚙️ Configuration

You can easily customize the script's behavior to fit your network environment by editing the variables at the top of `cf_scanner.py`:

| Variable | Default | Description |
| --- | --- | --- |
| `FILE_NAME` | `'export.ipv4'` | The input file containing your CIDR ranges. |
| `OUTPUT_FILE` | `'vless_working_ips.txt'` | The file where the working, sorted IPs will be saved. |
| `TARGET_WORKING_IPS` | `10` | The script halts automatically once it finds this many working IPs. |
| `SAMPLES_PER_SUBNET` | `2` | Number of random IPs to test from *each* subnet block. |
| `MAX_THREADS` | `100` | Concurrent threads. *Lower this if your router struggles with high connections.* |
| `VLESS_PORT` | `443` | The target TCP port (443 is standard for TLS VLESS). |
| `TIMEOUT` | `1.5` | Max seconds to wait for a connection before marking the IP as dead/blocked. |

---

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

---

## ⚠️ Disclaimer

This tool is intended for personal network optimization and educational purposes. Please ensure you have permission to scan the target IP ranges and adhere to your ISP's terms of service.
