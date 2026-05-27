# 🚀 True Latency & Speed Xray IP Scanner (v2.0)

A powerful, multithreaded Python script designed to hunt down the lowest-latency, highest-bandwidth working IP addresses from large CIDR lists (e.g., Cloudflare IP ranges).

Unlike standard ICMP ping tools or basic TCP socket checkers, this script **spawns actual Xray-core instances**. It dynamically injects test IPs into your personal VLESS/VMess configuration, routes real HTTP traffic through them, and **downloads a test payload to calculate actual Megabits per second (Mbps)**. This guarantees that the IPs you find are not just online, but are actively bypassing restrictions and providing high-speed proxy connections.

---

## ✨ Features

* **🎯 True Proxy Latency & Speed:** Tests actual proxy connections by first checking HTTP latency, then downloading a 150KB payload from Cloudflare to measure real-world throughput (Mbps).
* **📊 Exhaustive Search & Smart Sorting:** Tests your entire target list of IPs, then mathematically sorts the results to save only the absolute fastest connections (lowest ping + highest speed) rather than stopping at the first one that connects.
* **📡 Live Thread-Safe Console:** Watch the scanner work in real-time with a clean, synchronized terminal feed. No more messy timeout errors or overlapping text.
* **🔗 Auto-Generated Share Links:** Automatically extracts your UUID, SNI, and paths to create ready-to-use `vless://` URLs appended with Ping and Speed metrics. Just copy and paste them directly into v2rayN, v2rayNG, or Nekobox!
* **🛡️ Default Sanity Check:** Automatically tests your default `config.json` IP first to ensure your UUID, SNI, and paths are correct before wasting time scanning thousands of IPs.
* **⚡ Resource Managed & Collision-Free:** Runs a controlled number of concurrent Xray subprocesses with mathematically unique ports to prevent collisions. Automatically sweeps and deletes temporary JSON files upon exit.
* **📦 Zero Dependencies:** Built entirely with Python's standard library. No `requirements.txt` or `pip install` needed—just download and run!

---

## 📋 Prerequisites

* Python 3.6 or higher.
* The official **Xray-core** executable for your operating system.
* A text file containing IPv4 CIDR ranges (e.g., `export.ipv4`).
* Your working V2ray/Xray client configuration in JSON format.

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/PooryaSN2000/CF_Scanner.git
cd CF_Scanner

```

### 2. Download Xray-Core

Download the latest Xray-core release from the [official Project X GitHub](https://github.com/XTLS/Xray-core/releases). Extract the `.zip` file and place the `xray.exe` (or `xray` on Linux/Mac) in the same directory as the script, or inside an `Xray-windows-64` folder.

### 3. Setup your Config & IP List

1. Rename the provided `config_template.json` to `config.json`.
2. Open `config.json` and replace the placeholder variables (`REPLACE_WITH_YOUR_UUID`, `REPLACE_WITH_YOUR_SNI_DOMAIN`, etc.) with your actual server details.
3. Ensure you have a file named `export.ipv4` containing your target IP subnets, one per line.

> **⚠️ SECURITY WARNING:** Never upload your personal `config.json` to GitHub! Make sure it is added to your `.gitignore` file.

### 4. Run the scanner

```bash
python cf_scanner.py

```

### 5. Import to your Client

Once the scan is finished, open the newly created **`vless_links.txt`** file. Highlight all the text, copy it, and paste it directly into your client (e.g., `Ctrl+V` in v2rayN) to instantly import your fastest IPs!

---

## ⚙️ Configuration

You can customize the script's behavior by editing the variables at the top of `cf_scanner.py`:

| Variable | Default | Description |
| --- | --- | --- |
| `FILE_NAME` | `'export.ipv4'` | The input file containing your CIDR ranges. |
| `OUTPUT_FILE` | `'working_ips.txt'` | The file where the top raw working IPs are saved. |
| `LINKS_FILE` | `'vless_links.txt'` | The file where the sorted `vless://` share URLs are saved for quick import. |
| `CONFIG_TEMPLATE_FILE` | `'config.json'` | Your base Xray configuration file. |
| `XRAY_PATH` | `'Xray-windows-64\\xray.exe'` | Path to your Xray executable. |
| `MAX_IPS_TO_TEST` | `200` | Total pool of randomized IPs to test exhaustively. |
| `TARGET_WORKING_IPS` | `5` | The script saves only this many of the absolute *best* IPs from the results. |
| `SAMPLES_PER_SUBNET` | `2` | Number of random IPs to mathematically sample from *each* subnet block. |
| `MAX_THREADS` | `5` | Concurrent Xray instances. *Keep this low (5-15) as spawning full binaries is heavy.* |
| `PING_TIMEOUT` | `5.0` | Strict max seconds to wait for Xray to establish a connection and fetch the ping header. |
| `SPEED_TIMEOUT` | `15.0` | Generous max seconds to wait for the script to download the payload for speed testing. |

---

## 🖥️ Example Output

```text
======================================================================
STEP 1: Testing default config.json address...
[*] Default IP found: a.psnkali.ir
[V] Default config is WORKING. Proceeding to scan for more...
======================================================================

STEP 2: Testing all 200 IPs to find the lowest ping...
[SCAN] 104.18.78.41    | Ping: 1390ms | Speed: 2.62 Mbps [SUCCESS]
--- Progress: 1/200 Checked | 1 Working IPs Found ---
[SCAN] 104.17.125.124  | Ping: 674 ms | Speed: 0.90 Mbps [SUCCESS]
--- Progress: 2/200 Checked | 2 Working IPs Found ---
[SCAN] 8.34.202.94     | Failed (Timeout / No Ping)
--- Progress: 3/200 Checked | 2 Working IPs Found ---
[SCAN] 66.81.247.11    | Ping: 711 ms | Speed: 2.22 Mbps [SUCCESS]
--- Progress: 4/200 Checked | 3 Working IPs Found ---

======================================================================
[*] Filtering complete. Here are the TOP 3 lowest ping connections:
IP Address         | Latency    | Download Speed
----------------------------------------------------------------------
104.17.125.124     | 674     ms | 0.90 Mbps
66.81.247.11       | 711     ms | 2.22 Mbps
104.18.78.41       | 1390    ms | 2.62 Mbps
======================================================================
[*] Done. Top 3 raw IPs saved to working_ips.txt
[*] Done. Top 3 VLESS configs sorted by ping saved to vless_links.txt

```

---

## ⚠️ Disclaimer

This tool is intended for personal network optimization and educational purposes. Please ensure you have permission to scan the target IP ranges and adhere to your ISP's terms of service.