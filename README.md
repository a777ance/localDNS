# localDNS 2.0 ◈ Private Networking, Performance & Monitoring Stack

A clean-slate, consolidated, hyper-efficient "Infrastructure-as-Code" snapshot for a home network server running on an **HP t630 thin client** (or any Ubuntu 24.04 box). Every configuration, container, and system service is organized into a clean, 4-category layout—stripped of bloated, static documentation that is now handled dynamically.

---

## 🌐 The Interactive Front-End (GitHub Pages)
To eliminate stale, manual, and error-prone setup guides, the interactive components, calculators, and detailed business walkthroughs have been offloaded to our live, reactive web pages:

*   **⚡ [Home DNS — Interactive Field Guide](https://a777ance.github.io/Home-Sovereign-Full-Field-Guide/)**: A fully reactive setup wizard (Steps 0–11). Toggle your WAN configs, enter your LAN IP, username, and interface name—**every terminal command on the page live-updates to match your home environment**, tracking your progress locally.
*   **📊 [Guild Ledger Master Amounts Calculator](https://a777ance.github.io/PRICING-MODELS---ALL-THREE/)**: An interactive ledger that handles financial calculations, revenue splits, COGS, storefront hardware margins, and founder/operator hourly rates.
*   **📋 [Full End-to-End Business Playbook](https://a777ance.github.io/DESIGN-Full-Workflow-Integration-end-to-end-/)**: Maps the stranger-to-lead-to-customer-to-operator lifecycle that drives the private monthly Network Activity Statement.
*   **📣 [Marketing Strategy](https://a777ance.github.io/Marketing-Strategy-1/)**: The go-to-market and outreach playbook — positioning, channels, and campaign planning for the stack.

---

## 📂 Repository Architecture (Consolidated 2.0 Layout)

The repository is divided into **four clean categories** based on service boundaries rather than installation chronology:

```text
localdns/
├── 01-core-network/                  # Secure DNS, firewall, and remote access
│   ├── unbound/                      # Recursive, DNSSEC-validated DNS + cache dump scripts
│   ├── pihole/                       # Pi-hole ad-blocking container engine
│   ├── host-dns/                     # Fix to prevent systemd-resolved port 53 collisions
│   ├── ufw/                          # Default-deny host/network firewall ruleset
│   └── wireguard/                    # WireGuard server configuration and peer templates
│
├── 02-performance/                   # Hardware and link queue tuning
│   ├── cake/                         # CAKE SQM bufferbloat control and systemd unit
│   └── gpu-performance/              # GPU & CPU power governors for headless thin clients
│
├── 03-monitoring/                    # Observability and cron alert mechanisms
│   ├── uptime-kuma/                  # Uptime Kuma container configuration
│   └── monitors/                     # Cron-triggered packet loss and queue latency checks
│
├── 04-user-services/                 # Self-hosted user applications
│   ├── console/                      # Odin's High Seat launcher and ttyd web terminals
│   ├── ai-orchestration/             # LiteLLM router and Open WebUI containers
│   └── remote-desktop/               # NoMachine server tuning files
│
├── tools/                            # Repo maintenance & verification tools
└── CLAUDE.md                         # Structural guide and deploy references for AI assistants
