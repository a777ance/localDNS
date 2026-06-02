# CLAUDE.md

Briefing for Claude Code. Read this first — it is the authoritative summary of
the whole system. SETUP.md is the step-by-step reproduction guide.
network-context.md has detailed rationale for non-obvious design decisions.

---

## What this repo is

Config snapshot and rollback target for a self-hosted DNS + monitoring + VPN
stack on an HP t630 thin client. Every file maps to a specific location on the
live system (see "Deploy paths" below). Edits here do not take effect until
manually deployed.

**The live t630 is the source of truth.** When in doubt, SSH to `192.168.1.118`.

---

## Hardware

- **HP t630** — AMD Carrizo GX-420GI quad-core, 16 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired only — Wi-Fi disabled)

---

## Network topology

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
| Mac | 10.8.0.7 | |

**Services**

| Service | Runtime | Port(s) | Accessible from |
| ------- | ------- | ------- | --------------- |
| Pi-hole | Docker bridge | 53 (DNS), 8080 (UI) | LAN + WG subnet |
| Unbound | host OS | 5335 | Pi-hole only (via `172.17.0.1`) |
| Uptime Kuma | Docker host-net | 3001 | LAN + WG subnet |
| WireGuard | host OS | 51820/UDP | Internet (open to Anywhere) |
| NoMachine | host OS | 4000 | LAN only |
| xrdp | host OS | 3389 | LAN only |
| SSH | host OS | 22 | LAN + WG subnet |

**Pi-hole upstream DNS:** a single upstream — `172.17.0.1#5335` (Unbound, via the
Docker bridge gateway). Pi-hole does no resolver selection of its own; it forwards
every query to Unbound. Set in Pi-hole UI (Settings → DNS); the compose env var
only seeds this on a fresh volume. Do not add public resolvers here — that would
race them for all queries and leak personal lookups.

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
the ISP in the clear. An interim plan to engulf a `cloudflared proxy-dns` organelle
was dropped — Cloudflare removed that feature in v2026.2.0 — in favor of Unbound's
native DoT. See network-context.md "Unbound DNS split".)

**Host's own DNS:** the t630 resolves its *own* queries (apt, git, curl) via external
resolvers (`systemd/resolved.conf.d/host-dns.conf`), NOT its own Pi-hole — it cannot
reach the Dockerized Pi-hole on `:53` from the host. See network-context.md "Host
resolver" for the root cause.

**Uptime Kuma** runs with `network_mode: host` so it can reach Unbound at
`127.0.0.1:5335` directly. No `ports:` mapping in the compose file.

---

## Deploy paths

Folders are numbered by installation order — folder name = step number in SETUP.md.

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `01-unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `01-unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `01-unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `01-unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `01-unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` | `sudo systemctl restart unbound` |
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

---

## Unbound config

Five drop-ins loaded alphabetically from `/etc/unbound/unbound.conf.d/`:

| File | Purpose |
| ---- | ------- |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `server.conf` | Interface, port, access-control, security flags |
| `streaming-forward.conf` | Forward-zones: streaming/media domains → Cloudflare over DoT (`1.1.1.1@853`, `forward-tls-upstream`); all else recursive. Sets `tls-cert-bundle` for upstream cert validation. |
| `tuning.conf` | All performance and cache values — single source of truth |

`tuning.conf` is the only place to change cache sizes, TTLs, or threading.
Do not split these into separate files.

To verify the DNS split: `sudo unbound-control lookup netflix.com` should show
`forwarding request` to `1.1.1.1@853`/`1.0.0.1@853`. `sudo unbound-control lookup
chase.com` should show iterative delegation to authoritative nameservers (no
forwarder). A resolved `dig @127.0.0.1 -p 5335 netflix.com +short` confirms the DoT
path works end-to-end (it fails closed to recursion via `forward-first` if :853 is
blocked).

---

## AMD Carrizo GPU

The iGPU downclocks to ~200 MHz headless. Four pieces, all required:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `systemd/gpu-performance.service`
3. `systemd/cpu-performance.service`
4. `udev/99-amdgpu-performance.rules` — re-asserts `high` on every DRM event

---

## Known issues

| Issue | Action |
| ----- | ------ |
| `WEBPASSWORD` in pihole compose | Placeholder — do not commit real credentials |
| Windows laptop WireGuard key | Exposed during setup; rotate before trusting this peer |
| WireGuard peers 10.8.0.4, 10.8.0.5, 10.8.0.6 | Present in live wg0.conf but not documented — identify devices and add to peer table |
| WireGuard `::/0` IPv6 black hole | Server is IPv4-only in-tunnel; peers routing `::/0` black-hole IPv6 (handshake OK, pages hang). Peer template now defaults to `0.0.0.0/0`. Leak-free dual-stack fix (ULA + NAT66) documented in network-context.md "WireGuard IPv6 black hole". |
| **UNRESOLVED:** VPN peer DNS over the tunnel | Phone (`10.8.0.2`) can't resolve via Pi-hole at `10.8.0.1`: queries reach `wg0` (tcpdump) but replies don't return; the laptop (`10.8.0.3`) does appear as a Pi-hole client, so it's intermittent. Likely the Dockerized Pi-hole `:53` path from the host's own interface IPs (same family as the host-resolver bug). First set Pi-hole listening mode to ALL (`pihole-FTL --config dns.listeningMode ALL` + restart); if still unanswered, run Pi-hole with `network_mode: host` like Uptime Kuma. Stopgap: point the peer's DNS at an external resolver (e.g. `1.1.1.1`). |
| Live Pi-hole upstreams ≠ repo | Dashboard shows the live Pi-hole forwarding directly to `8.8.8.8`/`8.8.4.4`/`9.9.9.9`/`149.112.112.112`/`208.67.222.222` **plus** `172.17.0.1#5335` — the old multi-resolver race retained in the `pihole_data` volume, not the single Unbound upstream the repo specifies. Re-set Pi-hole UI → Settings → DNS to the single `172.17.0.1#5335` so the streaming split (which lives in Unbound) is actually in effect. |

---

## Verification

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

## Working philosophy

Every commit to `main` must leave SETUP.md able to reproduce a working system on
clean Ubuntu 24.04. Use feature branches for half-finished work.

---

## Further reading

- **SETUP.md** — full step-by-step reproduction guide
- **network-context.md** — design rationale: Docker networking, UFW/WireGuard
  forwarding, CAKE bufferbloat scope, Uptime Kuma monitor stack

