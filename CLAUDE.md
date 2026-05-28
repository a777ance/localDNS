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

- **HP t630** — AMD Carrizo GX-420GI quad-core, 4 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired only — Wi-Fi disabled)

---

## Network topology

```
ISP (Spectrum ~180/100 Mbps)
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

**Pi-hole upstream DNS:** `172.17.0.1#5335` — the Docker bridge gateway to
Unbound on the host. Set this in Pi-hole UI (Settings → DNS) after first deploy;
the compose env var is only an initial default.

**Uptime Kuma** runs with `network_mode: host` so it can reach Unbound at
`127.0.0.1:5335` directly. No `ports:` mapping in the compose file.

---

## Deploy paths

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
| `uptime-kuma/docker-compose.yml` | `~/uptime-kuma/docker-compose.yml` | `cd ~/uptime-kuma && docker compose up -d` |
| `ufw/setup.sh` | run directly | `sudo bash ufw/setup.sh` |
| `wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` | `sudo systemctl restart wg-quick@wg0` |
| `wireguard/peer-template.conf` | reference only | — |
| `nomachine/server.cfg` | `/usr/NX/etc/server.cfg` | `sudo /usr/NX/bin/nxserver --restart` |
| `cake/setup.sh` | `/usr/local/sbin/cake-setup.sh` | `sudo systemctl restart cake` |
| `systemd/cake.service` | `/etc/systemd/system/cake.service` | `sudo systemctl daemon-reload` |
| `systemd/gpu-performance.service` | `/etc/systemd/system/gpu-performance.service` | `sudo systemctl daemon-reload` |
| `systemd/cpu-performance.service` | `/etc/systemd/system/cpu-performance.service` | `sudo systemctl daemon-reload` |
| `systemd/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `systemd/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `systemd/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `scripts/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `scripts/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `scripts/packet-loss-monitor.sh` | `~/packet-loss-monitor.sh` (+ cron) | `crontab -e` |
| `udev/99-amdgpu-performance.rules` | `/etc/udev/rules.d/99-amdgpu-performance.rules` | `sudo udevadm control --reload-rules` |

---

## Unbound config

Four drop-ins loaded alphabetically from `/etc/unbound/unbound.conf.d/`:

| File | Purpose |
| ---- | ------- |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `server.conf` | Interface, port, access-control, security flags |
| `tuning.conf` | All performance and cache values — single source of truth |

`tuning.conf` is the only place to change cache sizes, TTLs, or threading.
Do not split these into separate files.

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

---

## Verification

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec   # 'ad' flag = DNSSEC working
docker ps                                       # pihole + uptime-kuma both Up
sudo wg show                                    # wg0 up, peers listed
sudo ufw status verbose                         # 51820/udp Anywhere; all else LAN
tc qdisc show dev enp1s0                        # cake bandwidth 90Mbit
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
