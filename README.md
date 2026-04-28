# 🎯 Continuous Attack Surface Management (ASM) Pipeline

An automated, distributed reconnaissance framework designed for Bug Bounty Hunters and Red Teamers. This pipeline continuously monitors target domains, discovers new assets, verifies their live status, and sends real-time alerts to Discord/Slack when infrastructure changes are detected.

## 🚀 Features
* **Automated Subdomain Enumeration:** Utilizes `subfinder` to map the target's external attack surface.
* **Live Asset Probing:** Verifies active web servers using `httpx`.
* **Stateful Diffing Engine:** Uses an SQLite database to compare current scans against historical data, ensuring you only get alerted for *new* findings.
* **CI/CD Integration:** Fully automated via GitHub Actions with persistent caching.
* **Real-time Alerting:** Webhook integrations for instant notification of newly spun-up subdomains.

## 🛠️ Tech Stack
* **Language:** Python 3.10
* **Tools:** Subfinder, httpx (ProjectDiscovery)
* **Infrastructure:** Docker, GitHub Actions
* **Storage:** SQLite3

## ⚙️ Setup & Usage
1. **Fork** this repository.
2. Go to your repository **Settings** > **Secrets and variables** > **Actions**.
3. Add a New Repository Secret named `DISCORD_WEBHOOK` with your channel's webhook URL.
4. Modify `TARGET_DOMAIN` in `.github/workflows/asm.yml` to your bug bounty target.
5. Go to the **Actions** tab and trigger the workflow manually to establish the baseline!

## 🔮 Future Roadmap (WIP)
- [ ] Integrate `Nuclei` for automated vulnerability scanning on new assets.
- [ ] Port the diffing engine to PostgreSQL/Redis for enterprise scale.
- [ ] Add `Amass` for deeper ASN and brute-force enumeration.
