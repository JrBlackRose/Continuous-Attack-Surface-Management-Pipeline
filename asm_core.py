import subprocess
import sqlite3
import requests
import os
import json
from datetime import datetime

# --- CONFIGURATION ---
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "example.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
DB_PATH = os.getenv("DB_PATH", "/app/data/asm_state.db") 
SUBS_FILE = "/app/data/subs.txt"
NEW_SUBS_FILE = "/app/data/new_subs.txt"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS assets
                 (subdomain TEXT UNIQUE, is_alive BOOLEAN, first_seen TEXT)''')
    conn.commit()
    return conn

def run_tool(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running command {command}: {e.stderr}")
        return []

def send_alert(new_assets, vulnerabilities=None):
    if not WEBHOOK_URL or not new_assets:
        return
    
    message = f"🚨 **New Assets Discovered for {TARGET_DOMAIN}** 🚨\n"
    for asset in new_assets:
        message += f"- `{asset}`\n"
        
    if vulnerabilities:
        message += "\n🔥 **Nuclei Vulnerabilities Detected!** 🔥\n"
        for vuln in vulnerabilities:
            message += f"- {vuln}\n"
    
    payload = {"content": message}
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("[+] Alert sent successfully.")
    except Exception as e:
        print(f"[!] Failed to send alert: {e}")

def main():
    print(f"[{datetime.now()}] Starting ASM Pipeline for {TARGET_DOMAIN}")
    conn = init_db()
    c = conn.cursor()

    # Step 1: Subdomain Enumeration
    print("[*] Running Subfinder...")
    subdomains = run_tool(f"subfinder -d {TARGET_DOMAIN} -silent")
    
    if not subdomains:
        print("[-] No subdomains found. Exiting.")
        return

    with open(SUBS_FILE, "w") as f:
        f.write("\n".join(subdomains))

    # Step 2: Alive Checking
    print("[*] Running httpx...")
    alive_assets = run_tool(f"httpx -l {SUBS_FILE} -silent")

    # Step 3: Diffing
    new_findings = []
    for asset in alive_assets:
        c.execute("SELECT * FROM assets WHERE subdomain=?", (asset,))
        if not c.fetchone():
            new_findings.append(asset)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO assets (subdomain, is_alive, first_seen) VALUES (?, ?, ?)", 
                      (asset, True, timestamp))
    
    # Step 4: Vulnerability Scanning & Alerting
    if new_findings:
        print(f"[+] Found {len(new_findings)} new live assets!")
        
        # Save new findings to a file for Nuclei to consume
        with open(NEW_SUBS_FILE, "w") as f:
            f.write("\n".join(new_findings))
            
        print("[*] Running Nuclei on newly discovered assets...")
        # Run Nuclei looking for exposures, cves, and misconfigs. Output as JSON lines.
        nuclei_cmd = f"nuclei -l {NEW_SUBS_FILE} -t http/cves,http/exposures,http/vulnerabilities -severity high,critical -jsonl -silent"
        nuclei_output = run_tool(nuclei_cmd)
        
        vulns = []
        for line in nuclei_output:
            try:
                data = json.loads(line)
                severity = data.get('info', {}).get('severity', 'UNKNOWN').upper()
                name = data.get('info', {}).get('name', 'Unknown')
                matched_at = data.get('matched-at', 'Unknown')
                vulns.append(f"**[{severity}]** {name} found at `{matched_at}`")
            except json.JSONDecodeError:
                continue

        send_alert(new_findings, vulns)
        conn.commit()
    else:
        print("[-] No new assets discovered this run.")

    conn.close()
    print(f"[{datetime.now()}] Pipeline finished.")

if __name__ == "__main__":
    main()
