# localDNS 2.0 ◈ Private Networking, Performance & Monitoring Stack

A clean-slate, consolidated, hyper-efficient "Infrastructure-as-Code" snapshot for a home network server running on an **HP t630 thin client** (or any Ubuntu 24.04 box). Every configuration, container, and system service is organized into a clean, 4-category layout—stripped of bloated, static documentation that is now handled dynamically.

---

## 🌐 The Interactive Front-End (GitHub Pages)
To eliminate stale, manual, and error-prone setup guides, the interactive components, calculators, and detailed business walkthroughs have been offloaded to our live, reactive web pages:

*   **⚡ [Home DNS — Interactive Field Guide](https://a777ance.github.io/Home-Sovereign-Full-Field-Guide/)**: A fully reactive setup wizard (Steps 0–11). Toggle your WAN configs, enter your LAN IP, username, and interface name—**every terminal command on the page live-updates to match your home environment**, tracking your progress locally.
*   **📊 [Guild Ledger Master Amounts Calculator](https://a777ance.github.io/PRICING-MODELS---ALL-THREE/)**: An interactive ledger that handles financial calculations, revenue splits, COGS, storefront hardware margins, and founder/operator hourly rates.
*   **📋 [Full End-to-End Business Playbook](https://a777ance.github.io/DESIGN-Full-Workflow-Integration-end-to-end-/)**: Maps the stranger-to-lead-to-customer-to-operator lifecycle that drives the private monthly Network Activity Statement.
*   **🧾 [Network Activity Statement Gallery](https://a777ance.github.io/localDNS/)**: This repo's own Pages site (published from `docs/statements/` by the `pages.yml` workflow) — an installable PWA gallery of the client-facing Network Activity Statements and the operator-side Alliance Member Portfolio.
*   **🦊 [Firefox Hardening — Field Guide](https://a777ance.github.io/localDNS/firefox-hardening.html)**: Conform any Firefox profile to the house endpoint posture — paths that rewrite themselves for snap/native/flatpak/macOS/Windows, copy-paste install, verification, and the expected breakage. Explains why the endpoint is strict on fingerprinting and WebRTC but relaxed on session sanitisation: the network layer already holds that ground. Canonical source: `04-user-services/endpoint-hardening/`.
*   **🌈 [Bifrost — the command-notation schema](https://a777ance.github.io/localDNS/bifrost.html)**: The A777ance keyboard-spatial command-composition schema — the `~ ! @ # $ % ^ & * ()` "highway" — published from this repo's `docs/bifrost.html` alongside the gallery. Canonical spec: `04-user-services/ai-orchestration/highway-notation.md`.
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
│   ├── remote-desktop/               # NoMachine server tuning files
│   ├── console/                      # High Seat launcher + ttyd web terminals (units + page; verify vs live box)
│   └── ai-orchestration/             # jury/ + jury-claude/ voters + LiteLLM front door; langgraph-router (Odin) still NOT in repo
│
├── vault/                            # sops+age secrets tooling (seal/unseal/rotate; sealed *.env.sops)
├── tools/                            # Repo maintenance & verification tools (check-docs.py, migrate.sh)
└── CLAUDE.md                         # Structural guide and deploy references for AI assistants
```

> **Not yet snapshotted.** These are live on the t630 but not checked in, so the repo
> is not yet a complete rollback target for them. Track them down and add them:
>
> - `04-user-services/ai-orchestration/langgraph-router/` — the Odin supervisor (the LiteLLM front door and the `jury/` / `jury-claude/` voters are already in the repo)
> - the sealed `vault/*.env.sops` files — the sops+age tooling (`vault/`) is in the repo; the sealed secrets themselves are created from the real values on the box
>
> See CLAUDE.md § C ("drift to reconcile") for the full mapping.

---

## 🚀 Deploying to the live box

Two documents, one job — getting config from this repo onto the t630:

*   **⚙️ [docs/DEPLOY-PROTOCOL.md](docs/DEPLOY-PROTOCOL.md) — the *how*.** The repeatable
    per-change procedure (sync → diff → back up → validate → reload → verify the
    *effect*). Read it before you `cp` anything onto the box.
*   **📋 [docs/DEPLOY-QUEUE.md](docs/DEPLOY-QUEUE.md) — the *what*.** The staged backlog of
    config fixed in the repo but not yet applied to the live t630, in dependency order.
    Each stage runs the protocol above.
