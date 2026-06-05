# CLAUDE.md

Briefing for Claude Code. Read this first — it is the authoritative summary of
the whole system. README.md is the complete setup guide and system reference.
network-context.md has detailed rationale for non-obvious design decisions.

---

## House style: ordering & typography

These conventions apply across **every** A777ance repo — current and future. (Adopted 2026-06-05.)

- **Time-based content reads newest-first (reverse-chronological).** Logs, changelogs,
  decision logs (ADR / FIN), known-issues and issue trackers, FAQs, metrics and review
  logs, and "Handled For You" entries all lead with the most recent item. Apply this
  within the time-based *section* even when the whole file isn't time-based.
- **Alphabetical lists run Z → A** (descending).
- **Walkthroughs: reverse the blocks, keep the steps.** In a step-by-step guide, present
  the major sections/blocks in reverse order (last block first — it helps "block" the
  work), but keep the numbered steps *within* each block in forward order so every
  procedure stays followable. A walkthrough's table of contents mirrors the reversed
  block order. **Never renumber** — step and stage numbers stay fixed, so the intended
  execution order is always readable from the numbers.
- **Font: Gill Sans MT everywhere.** Every surface — customer-facing or internal — uses
  Gill Sans MT. Web/CSS stack:
  `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

---

## Contents

- [House style: ordering & typography](#house-style-ordering--typography)
- [0. What this repo is](#0-what-this-repo-is)
- [A. Hardware](#a-hardware)
- [B. Network topology](#b-network-topology)
- [C. Deploy paths](#c-deploy-paths)
- [D. Unbound config](#d-unbound-config)
- [E. AMD Carrizo GPU](#e-amd-carrizo-gpu)
- [1. Known issues](#1-known-issues)
- [2. Verification](#2-verification)
- [3. Working philosophy](#3-working-philosophy)
- [4. Further reading](#4-further-reading)
- [5. AI CTO state](#5-ai-cto-state)

---

## 0. What this repo is

Config snapshot and rollback target for a self-hosted DNS + monitoring + VPN
stack on an HP t630 thin client. Every file maps to a specific location on the
live system (see "Deploy paths" below). Edits here do not take effect until
manually deployed.

**The live t630 is the source of truth.** When in doubt, SSH to `192.168.1.118`.

---

## A. Hardware

- **HP t630** — AMD Carrizo GX-420GI quad-core, 16 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired only — Wi-Fi disabled)

---

## B. Network topology

```
ISP (Spectrum ~200/100 Mbps asymmetric)
  │
  └── Netgear R7000     192.168.1.1    main router (routing, NAT, DHCP, WAN)
        │
        └── t630        192.168.1.118  DNS + VPN server (DHCP reservation)
              │
              └── wg0   10.8.0.1/24   WireGuard tunnel interface
```

**WireGuard peers**

| Peer | Tunnel IP | Notes |
| ---- | --------- | ----- |
| t630 wg0 | 10.8.0.1 | Server gateway; DNS address peers use |
| iPhone | 10.8.0.2 | |
| Windows laptop | 10.8.0.3 | Key rotation needed — see Known issues |
| (unidentified) | 10.8.0.4–10.8.0.6 | In wg0.conf, no recent handshake — identify or remove |
| Mac | 10.8.0.7 | |

**Services**

| Service | Runtime | Port(s) | Accessible from |
| ------- | ------- | ------- | --------------- |
| Pi-hole | Docker host-net | 53 (DNS), 8080 (UI) | LAN + WG subnet |
| Unbound | host OS | 5335 | Pi-hole only (via `127.0.0.1`) |
| Uptime Kuma | Docker host-net | 3001 | LAN + WG subnet |
| WireGuard | host OS | 51820/UDP | Internet (open to Anywhere) |
| NoMachine | host OS | 4000 | LAN only |
| xrdp | host OS | 3389 | LAN only |
| SSH | host OS | 22 | LAN + WG subnet |
| LLM router (LiteLLM) | Docker host-net | 4040 | LAN + WG subnet |
| Open WebUI (LLM chat UI) | Docker host-net | 3000 | LAN + WG subnet |

**Pi-hole upstream DNS:** a single upstream — `127.0.0.1#5335` (Unbound on the host;
reachable directly because Pi-hole runs `network_mode: host`). Pi-hole does no
resolver selection of its own; it forwards every query to Unbound. Set via
`FTLCONF_dns_upstreams` in the compose file (Pi-hole v6 re-applies and locks it on
every start; visible read-only in the UI under Settings → DNS). Do not add public
resolvers here — that would race them for all queries and leak personal lookups.

**DNS resolution strategy (the split lives in Unbound):** `streaming-forward.conf`
is the single decision point. High-volume/low-sensitivity domains (Netflix,
YouTube, Spotify, Steam, etc.) are forwarded to **Cloudflare over DNS-over-TLS**
(`1.1.1.1@853#cloudflare-dns.com` / `1.0.0.1`, `forward-tls-upstream: yes`), so the
ISP sees an encrypted channel instead of cleartext lookups — trading privacy for
speed on traffic whose destination is not sensitive. Everything else (personal,
sensitive, default) resolves recursively through Unbound with DNSSEC — Cloudflare
never sees these queries. **Invariant:** never add sensitive domains to the
forward-path; that would hand Cloudflare your private lookups. (This path previously
forwarded to a ~18-resolver plaintext UDP/53 pool, which leaked streaming lookups to
the ISP in the clear. An interim plan to run a local `cloudflared proxy-dns` daemon
was dropped — Cloudflare removed that feature in v2026.2.0 — in favor of Unbound's
native DoT. See network-context.md "Unbound DNS split".)

**Host's own DNS:** the t630 resolves its *own* queries (apt, git, curl) via external
resolvers (`03-host-dns/host-dns.conf`), NOT its own Pi-hole. Host-net Pi-hole takes
`0.0.0.0:53` (so the resolved stub is disabled, `DNSStubListener=no`), and
`/etc/resolv.conf` can't carry Unbound's `:5335` — so the host points straight at
`9.9.9.9`/`1.1.1.1` instead. See network-context.md "Host resolver" for the root cause.

**Uptime Kuma** runs with `network_mode: host` so it can reach Unbound at
`127.0.0.1:5335` directly. No `ports:` mapping in the compose file. Pi-hole is
host-networked for the same reason (and so it answers VPN peers over `wg0`), so
both containers sit directly on the host network stack.

---

## C. Deploy paths

Folders are numbered by installation order. README adds two folder-less steps
(Step 0 Router, Step 3 Docker CE), so a folder's number is not its README step
number — use this table to map repo path → system path, not the step numbers.

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `01-unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `01-unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `01-unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `01-unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `01-unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` | `sudo systemctl restart unbound` |
| `01-unbound/local-records.conf` | `/etc/unbound/unbound.conf.d/local-records.conf` | `sudo systemctl restart unbound` |
| `01-unbound/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `01-unbound/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `01-unbound/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `01-unbound/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `01-unbound/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `02-pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
| `03-host-dns/host-dns.conf` | `/etc/systemd/resolved.conf.d/host-dns.conf` | `sudo systemctl restart systemd-resolved` |
| `04-ufw/setup.sh` | run directly | `sudo bash 04-ufw/setup.sh` |
| `05-wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` | `sudo systemctl restart wg-quick@wg0` |
| `05-wireguard/peer-template.conf` | reference only | — |
| `06-cake/setup.sh` | `/usr/local/sbin/cake-setup.sh` | `sudo systemctl restart cake` |
| `06-cake/cake.service` | `/etc/systemd/system/cake.service` | `sudo systemctl daemon-reload` |
| `07-uptime-kuma/docker-compose.yml` | `~/uptime-kuma/docker-compose.yml` | `cd ~/uptime-kuma && docker compose up -d` |
| `07-uptime-kuma/packet-loss-monitor.sh` | `~/packet-loss-monitor.sh` (+ cron) | `crontab -e` |
| `07-uptime-kuma/cake-monitor.sh` | `~/cake-monitor.sh` (+ cron) | `crontab -e` |
| `08-gpu-performance/gpu-performance.service` | `/etc/systemd/system/gpu-performance.service` | `sudo systemctl daemon-reload` |
| `08-gpu-performance/cpu-performance.service` | `/etc/systemd/system/cpu-performance.service` | `sudo systemctl daemon-reload` |
| `08-gpu-performance/99-amdgpu-performance.rules` | `/etc/udev/rules.d/99-amdgpu-performance.rules` | `sudo udevadm control --reload-rules` |
| `09-remote-desktop/server.cfg` | `/usr/NX/etc/server.cfg` | `sudo /usr/NX/bin/nxserver --restart` |
| `10-llm-router/docker-compose.yml` | `~/llm-router/docker-compose.yml` | `cd ~/llm-router && docker compose up -d` |
| `10-llm-router/config.yaml` | `~/llm-router/config.yaml` | `cd ~/llm-router && docker compose up -d` |
| `10-llm-router/.env.example` | `~/llm-router/.env` (copy, then fill in) | `cd ~/llm-router && docker compose up -d` |
| `docs/statements/tools/collect/nftables-accounting.nft` | load with `sudo nft -f nftables-accounting.nft` | re-run anytime (idempotent) |
| `docs/statements/tools/collect/populate_sets.py` | `~/a777ance/collect/populate_sets.py` (+ cron `3 */6 * * *`) | `crontab -e` |
| `docs/statements/tools/collect/collect_stats.py` | `~/a777ance/collect/collect_stats.py` (+ cron `30 0 * * *`) | `crontab -e` |

---

## F. nftables volume layer — deploy checklist

Run this once on the t630 to stand up per-category byte accounting. All four
steps can be done in one SSH session.

```bash
# 1. Copy the collect tools to the box (from your machine)
scp -r docs/statements/tools/collect/ user@192.168.1.118:~/a777ance/collect/

# 2. Load the accounting ruleset (idempotent — safe to re-run)
sudo nft -f ~/a777ance/collect/nftables-accounting.nft
sudo nft list table inet a777acct          # sets + counters exist, all zero — expected

# 3. Dry-run the set populator (resolves DNS, touches nothing)
python3 ~/a777ance/collect/populate_sets.py | head

# 4. Apply for real (programs the IP sets; counters start counting)
sudo python3 ~/a777ance/collect/populate_sets.py --apply
sudo nft -j list counters table inet a777acct   # should show non-zero bytes within minutes

# 5. Add to cron (crontab -e)
# refresh IP sets every 6h (CDN IPs rotate; elements time out in 24h)
3 */6 * * *  sudo /usr/bin/python3 /home/USER/a777ance/collect/populate_sets.py --apply >/dev/null 2>&1
# collect monthly stats nightly
30 0 * * *   /usr/bin/python3 /home/USER/a777ance/collect/collect_stats.py \
             --out /var/lib/a777ance/$(date +\%Y-\%m).stats.json
```

Replace `USER` with the actual username on the t630. After the cron runs once,
verify with: `sudo nft -j list counters table inet a777acct`

---

## D. Unbound config

Six drop-ins, loaded alphabetically (A→Z) by Unbound from `/etc/unbound/unbound.conf.d/`
— listed Z→A here per house style:

| File | Purpose |
| ---- | ------- |
| `tuning.conf` | All performance and cache values — single source of truth |
| `streaming-forward.conf` | Forward-zones: streaming/media domains → Cloudflare over DoT (`1.1.1.1@853`, `forward-tls-upstream`); all else recursive. Sets `tls-cert-bundle` for upstream cert validation. |
| `server.conf` | Interface, port, access-control, security flags |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `local-records.conf` | LAN-only A records answered authoritatively (`ai.home.lan` → the t630, for the LLM router). `local-zone … transparent` overrides only the names defined, not the whole zone. |

`tuning.conf` is the only place to change cache sizes, TTLs, or threading.
Do not split these into separate files.

To verify the DNS split: `sudo unbound-control lookup netflix.com` should show
`forwarding request` to `1.1.1.1@853`/`1.0.0.1@853`. `sudo unbound-control lookup
chase.com` should show iterative delegation to authoritative nameservers (no
forwarder). A resolved `dig @127.0.0.1 -p 5335 netflix.com +short` confirms the DoT
path works end-to-end (it fails closed to recursion via `forward-first` if :853 is
blocked).

---

## E. AMD Carrizo GPU

The iGPU downclocks to ~200 MHz headless. Four pieces, all required:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `08-gpu-performance/gpu-performance.service`
3. `08-gpu-performance/cpu-performance.service`
4. `08-gpu-performance/99-amdgpu-performance.rules` — re-asserts `high` on every DRM event

---

## 1. Known issues

| Issue | Action |
| ----- | ------ |
| Live Pi-hole upstreams ≠ repo | Pi-hole v6 re-applies & locks `FTLCONF_dns_upstreams: 127.0.0.1#5335` on every start, overriding any `172.17.0.1#5335`/public resolvers left in the `pihole_data` volume. Confirm in the UI after deploying onto an old volume. |
| Host-net Pi-hole vs systemd-resolved `:53` | Host-net Pi-hole binds `0.0.0.0:53`, colliding with the resolved stub on `127.0.0.53:53`. `03-host-dns/host-dns.conf` now sets `DNSStubListener=no` and README Steps 4-5 (Part A) re-points `/etc/resolv.conf` off the stub. On the live box, check current state before re-applying (see INSTALL-NOTES item 13). |
| VPN peer DNS over the tunnel | **Resolved.** Pi-hole switched to `network_mode: host` — Docker DNAT no longer in the path, so `10.8.0.1:53` is answered directly for queries sourced from `wg0`. Port 8080 also added to the WG UFW rules so the Pi-hole UI is reachable from VPN peers. |
| WireGuard `::/0` IPv6 black hole | Server is IPv4-only in-tunnel; peers routing `::/0` black-hole IPv6 (handshake OK, pages hang). Peer template now defaults to `0.0.0.0/0`. Leak-free dual-stack fix (ULA + NAT66) documented in network-context.md "WireGuard IPv6 black hole". |
| WireGuard peers 10.8.0.4, 10.8.0.5, 10.8.0.6 | Now reconciled into `05-wireguard/wg0.conf` (real public keys) but still UNIDENTIFIED with no recent handshake — identify each device or remove the stale peer. |
| Windows laptop WireGuard key | Exposed during setup; rotate before trusting this peer |
| Pi-hole v5 → v6 env vars | `pihole/pihole:latest` is v6; compose migrated from v5 vars (`WEBPASSWORD`, `WEB_PORT`, `PIHOLE_DNS_`) to `FTLCONF_*`. The v5 names are silently ignored by v6. |
| `FTLCONF_webserver_api_password` in pihole compose | Placeholder (`CHANGE_ME`) — do not commit real credentials |
| LLM router port vs NoMachine | The router (LiteLLM, stage 10) listens on **4040**, not LiteLLM's default 4000 — NoMachine already holds 4000 on this box. UFW gates 4040 to LAN + WG. |
| LLM router secrets (`~/llm-router/.env`) | `LITELLM_MASTER_KEY` + `ANTHROPIC_API_KEY` live in `.env` (git-ignored); repo ships `.env.example` with `CHANGE_ME`. Never commit the real keys. |
| Open WebUI port + first-run admin | Chat UI on **3000** (8080 is the Pi-hole UI). First account created at `chat.home.lan:3000` becomes admin — create it from a trusted device. State in `~/llm-router/open-webui-data/`. |

---

## 2. Verification

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec        # 'ad' flag = DNSSEC working
dig @127.0.0.1 -p 5335 netflix.com +short          # DoT forward-path resolves end-to-end
sudo unbound-control lookup netflix.com            # forwarding request → 1.1.1.1@853 / 1.0.0.1@853
sudo unbound-control lookup chase.com              # should show: iterative delegation
docker ps                                          # pihole + uptime-kuma both Up
sudo wg show                                       # wg0 up, peers listed
sudo ufw status verbose                            # 51820/udp Anywhere; all else LAN
tc qdisc show dev enp1s0                           # cake bandwidth 85Mbit
sudo iptables -t mangle -L POSTROUTING -v | grep DSCP  # EF mark on sport 53
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # high
```

---

## 3. Working philosophy

Every commit to `main` must leave README.md able to reproduce a working system on
clean Ubuntu 24.04.

**Push to `main`, no branches** — founder's standing instruction (2026-06-05). Don't
open PRs or park work on feature branches for these repos; land each change as a
coherent, deployable commit straight on `main`.

---

## 4. Further reading

- **README.md** — complete setup guide and system reference (SETUP.md absorbed here)
- **INSTALL-NOTES.md** — fresh install simulation: every known break point and fix
- **SKILLS.md** — skills demonstrated by the stack, each mapped to proving artifacts
- **PLUGINS.md** — which Claude Code Directory plugins apply to this config repo (short
  answer: none of the business ones — keep it lean)
- **network-context.md** — design rationale: Docker networking, UFW/WireGuard
  forwarding, CAKE bufferbloat scope, Uptime Kuma monitor stack

---

## 5. AI CTO state

Read `docs/ai-cto/context.md` in this repo for current open items and component status.
The portfolio hub (cross-repo roadmap, decisions log, tech debt) lives in
`DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.
