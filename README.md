---

# 🚀 True Latency Xray IP Scanner

A powerful, multithreaded Python script designed to hunt down the lowest-latency working IP addresses from large CIDR lists (e.g., Cloudflare IP ranges).

Unlike standard ICMP ping tools or basic TCP socket checkers, this script **spawns actual Xray-core instances**. It dynamically injects test IPs into your personal VLESS/VMess configuration and routes real HTTP traffic through them. This guarantees that the IPs you find are not just online, but are actively bypassing restrictions and properly proxying traffic with your specific server settings.

---

## ✨ Features

* **🎯 True Proxy Latency:** Tests actual proxy connections by routing an HTTP request (via local proxy) through the Xray core, giving you the real-world delay.
* **🔗 Auto-Generated Share Links:** Automatically extracts your UUID, SNI, and paths to create ready-to-use `vless://` URLs. Just copy and paste them directly into v2rayN, v2rayNG, or Nekobox!
* **🛡️ Default Sanity Check:** Automatically tests your default `config.json` IP first to ensure your UUID, SNI, and paths are correct before wasting time scanning thousands of IPs.
* **🧠 Dynamic Config Injection:** Deep-copies your base configuration and securely swaps the target address and local ports in memory.
* **⚡ Resource Managed:** Runs a controlled number of concurrent Xray subprocesses to prevent system freezing, automatically cleaning up temporary JSON files and dead processes.
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
| `OUTPUT_FILE` | `'working_ips.txt'` | The file where the raw working IPs and latencies are saved. |
| `LINKS_FILE` | `'vless_links.txt'` | The file where the auto-generated `vless://` share URLs are saved for quick import. |
| `CONFIG_TEMPLATE_FILE` | `'config.json'` | Your base Xray configuration file. |
| `XRAY_PATH` | `'Xray-windows-64\\xray.exe'` | Path to your Xray executable. |
| `TARGET_WORKING_IPS` | `5` | The script halts automatically once it finds this many working IPs. |
| `SAMPLES_PER_SUBNET` | `2` | Number of random IPs to mathematically sample from *each* subnet block. |
| `MAX_THREADS` | `5` | Concurrent Xray instances. *Keep this low (5-15) as spawning full binaries is heavy.* |
| `TIMEOUT` | `5.0` | Max seconds to wait for Xray to establish a connection and fetch the test URL. |

---

## 🖥️ Example Output

```text
[*] Template Loaded. Xray Path: Xray-windows-64\xray.exe
==================================================
STEP 1: Testing your default config.json address...
[*] Default IP found in config: 104.18.223.224
[DEFAULT-CHECK] 104.18.223.224: Starting Xray on port 54321...
[DEFAULT-CHECK] 104.18.223.224: SUCCESS! Real Latency: 412ms
[V] Default config is WORKING. Proceeding to scan for more...
==================================================

STEP 2: Testing 20 IPs from export.ipv4...
[SCAN] 172.64.19.2: Starting Xray on port 54322...
[SCAN] 104.18.2.14: Starting Xray on port 54323...
[SCAN] 172.64.19.2: SUCCESS! Real Latency: 285ms
[SCAN] 104.18.2.14: SUCCESS! Real Latency: 310ms

[*] Target IP count reached.

==================================================
IP Address           | Latency
--------------------------------------------------
172.64.19.2          | 285ms
104.18.2.14          | 310ms
==================================================
[*] Done. Raw IPs saved to working_ips.txt
[*] Done. Copy-Paste Configs saved to vless_links.txt <--- IMPORT THESE!

```

---

## ⚠️ Disclaimer

This tool is intended for personal network optimization and educational purposes. Please ensure you have permission to scan the target IP ranges and adhere to your ISP's terms of service.