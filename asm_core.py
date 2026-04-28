import subprocess
import sqlite3
import requests
import os
from datetime import datetime

# --- CONFIGURATION ---
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "example.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
# Crucial: Allow overriding the DB path via env var so Docker can map it to our persistent folder
DB_PATH = os.getenv("DB_PATH", "/app/data/asm_state.db") 
SUBS_FILE = "/app/data/subs.txt"

def init_db():
    """Initializes the SQLite database to store our state."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS assets
                 (subdomain TEXT UNIQUE, is_alive BOOLEAN, first_seen TEXT)''')
    conn.commit()
    return conn

def run_tool(command):
    """Runs a shell command and returns the output as a list of lines."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running command {command}: {e.stderr}")
        return []

def send_alert(new_assets):
    """Sends a notification to a webhook (Discord/Slack)."""
    if not WEBHOOK_URL or not new_assets:
        return
    
    message = f"🚨 **New Assets Discovered for {TARGET_DOMAIN}** 🚨\n"
    for asset in new_assets:
        message += f"- `{asset}`\n"
    
    payload = {"content": message} # Discord format
    
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

    # Write subdomains to a file in the data directory
    with open(SUBS_FILE, "w") as f:
        f.write("\n".join(subdomains))

    # Step 2: Alive Checking (Probing)
    print("[*] Running httpx...")
    alive_assets = run_tool(f"httpx -l {SUBS_FILE} -silent")

    # Step 3: Diffing (The Magic)
    new_findings = []
    
    for asset in alive_assets:
        c.execute("SELECT * FROM assets WHERE subdomain=?", (asset,))
        if not c.fetchone():
            new_findings.append(asset)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO assets (subdomain, is_alive, first_seen) VALUES (?, ?, ?)", 
                      (asset, True, timestamp))
    
    # Step 4: Alerting and Committing
    if new_findings:
        print(f"[+] Found {len(new_findings)} new live assets!")
        send_alert(new_findings)
        conn.commit()
    else:
        print("[-] No new assets discovered this run.")

    conn.close()
    print(f"[{datetime.now()}] Pipeline finished.")

if __name__ == "__main__":
    main()
