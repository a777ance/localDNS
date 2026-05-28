# CLAUDE.md

Briefing for Claude Code. Read this file first; it is the authoritative summary
of the whole system. SETUP.md is the step-by-step reproduction guide.
network-context.md has deep operational rationale for non-obvious decisions.

---

## What this repo is

Config snapshot and rollback target for a self-hosted DNS + monitoring + VPN
stack running on an HP t630 thin client. Every file in the repo maps to a
specific location on the live system (see "Deploy paths" below). Edits here do
not take effect until manually deployed.

**The live t630 is the source of truth.** When in doubt about current state,
SSH to `192.168.1.118` and inspect the running system.

---

## Hardware

- **HP t630** thin client — AMD Carrizo GX-420GI quad-core, 4 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired Ethernet only — Wi-Fi disabled)

---

## Network topology

```
ISP (Spectrum ~180/100 Mbps)
  │
  └── Netgear R7000     192.168.1.1    main router: routing, NAT, DHCP, WAN
        │
        └── t630        192.168.1.118  DNS + VPN server (DHCP reservation, not static)
              │
              └── wg0   10.8.0.1/24   WireGuard tunnel interface
```

**WireGuard VPN peers**

| Peer | Tunnel IP | Notes |
| ---- | --------- | ----- |
| t630 (server) | 10.8.0.1 | Gateway; also the DNS address peers use |
| iPhone | 10.8.0.2 | |
| Windows laptop | 10.8.0.3 | KEY ROTATION NEEDED — private key was exposed during setup |
| Mac | 10.8.0.7 | |

**Services on the t630**

| Service | Process | Listens on | Port | Who reaches it |
| ------- | ------- | ---------- | ---- | -------------- |
| Pi-hole | Docker (bridge) | `0.0.0.0` | 53 (DNS), 8080 (UI) | LAN + WG subnet |
| Unbound | host OS | `0.0.0.0` | 5335 | Pi-hole only (via 172.17.0.1) |
| Uptime Kuma | Docker (host net) | `0.0.0.0` | 3001 | LAN + WG subnet |
| WireGuard | host OS | `0.0.0.0` | 51820/UDP | Internet (open to Anywhere) |
| NoMachine | host OS | `0.0.0.0` | 4000 | LAN only |
| xrdp (RDP) | host OS | `0.0.0.0` | 3389 | LAN only |
| SSH | host OS | `0.0.0.0` | 22 | LAN + WG subnet |

---

## Deploy paths

Every file in the repo and where it lives on the t630.

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
| `wireguard/peer-template.conf` | reference only — not deployed | — |
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

## Critical gotchas

**Pi-hole upstream DNS must be `172.17.0.1#5335`, not `127.0.0.1#5335`.**
Pi-hole runs inside a Docker bridge container. `127.0.0.1` inside the container is
the container's own loopback, not the host. The Docker bridge gateway (`172.17.0.1`)
is the host as seen from inside the container. The compose file sets the initial
value to `127.0.0.1#5335` — this is wrong and must be corrected in the Pi-hole UI
(Settings → DNS) after first deploy. The UI value persists in the Docker volume and
takes precedence on subsequent restarts.

**Pi-hole: "Permit all origins" must be checked.**
Without it, Pi-hole rejects queries from WireGuard peers (`10.8.0.x`) since they
aren't on the LAN subnet. This is safe because UFW restricts port 53 to
`192.168.0.0/16` and `10.8.0.0/24` — Pi-hole is never reachable from the internet.

**Uptime Kuma uses `network_mode: host`, NOT a Docker bridge.**
Required so it can reach Unbound at `127.0.0.1:5335`. Bridge networking makes
`127.0.0.1` point to the container's own loopback. With host networking the
`ports:` mapping is absent — Kuma binds directly on port 3001.

**WireGuard peer Address must be `/32`, not `/24`.**
`Address = 10.8.0.7/24` tells the OS the peer owns the whole `10.8.0.0/24` subnet —
routing breaks. `Address = 10.8.0.7/32` correctly says "this interface owns exactly
this one IP."

**WireGuard DNS field is IP only — no port.**
`DNS = 10.8.0.1` is correct. `DNS = 172.17.0.1:5335` silently fails; WireGuard
ignores port-qualified DNS entries. Also: `172.17.0.1` is the Docker bridge gateway
on the host and is not reachable from outside — use `10.8.0.1` (the wg0 interface).

**UFW must have `ufw default allow routed`** for WireGuard peer traffic to reach
the internet. Without it, UFW's FORWARD chain has a DROP policy and peer traffic
is silently dropped even when the tunnel handshakes successfully. Do NOT add raw
`iptables -A FORWARD` rules to wg0.conf PostUp — they land after UFW's DROP rule
and are never reached.

**SSH over VPN requires source-IP-aware UFW rules.**
When a VPN peer uses a full tunnel (`AllowedIPs = 0.0.0.0/0`), their source IP on
the server is `10.8.0.x`, not `192.168.x.x`. LAN-scoped UFW rules don't match.
Ports 22 and 3001 are allowed from `10.8.0.0/24` in `ufw/setup.sh` for this reason.
Use `ssh user@10.8.0.1` from a connected peer (always works via wg0 interface).

**CAKE on the t630 only shapes WireGuard traffic.**
The t630 is not inline for general LAN devices. Laptops/phones on Wi-Fi route
directly through the Netgear R7000 — CAKE on the t630 does not help them. For
whole-network SQM, the Netgear R7000 needs DD-WRT or FreshTomato with fq_codel.
See network-context.md "CAKE / bufferbloat" for the full comparison.

---

## Unbound config structure

Four drop-in files loaded alphabetically from `/etc/unbound/unbound.conf.d/`:

| File | What it does |
| ---- | ------------ |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `server.conf` | Interface binding, port, access-control, security flags |
| `tuning.conf` | All performance/cache values — single source of truth |

`tuning.conf` is the only place to change cache sizes, TTLs, or threading. Do not
reintroduce `performance.conf` or `ttl-override.conf` — they were consolidated into
`tuning.conf` to avoid split-brain between files.

---

## AMD Carrizo GPU remediation

The Carrizo iGPU downclocks to ~200 MHz with no display attached. Four pieces are
all required — removing any one of them causes the GPU to re-throttle:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `systemd/gpu-performance.service` — sets `high` at boot
3. `systemd/cpu-performance.service` — sets CPU governor to `performance`
4. `udev/99-amdgpu-performance.rules` — re-asserts `high` on every DRM event
   (display hotplug, runtime PM transitions — without this the GPU re-throttles
   mid-session even with the systemd services running)

---

## Working philosophy

Move toward truth, goodness, and elegance. Welcome clarity and correctness. Reject churn.
Every commit to `main` must leave SETUP.md able to reproduce a working system on
clean Ubuntu 24.04. Use feature branches for half-finished work.

---

## Load-bearing known issues

| Issue | Status |
| ----- | ------ |
| `PIHOLE_DNS_=127.0.0.1#5335` in compose | Wrong initial value — must fix in UI after first deploy. See Critical gotchas above. |
| `WEBPASSWORD` in compose | Placeholder only. Do not commit real credentials. |
| Windows laptop WireGuard key | Private key was shared in plaintext during setup. Key rotation required: delete tunnel, create new, re-add public key. |

---

## Verification

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec   # 'ad' flag = DNSSEC working
docker ps                                       # pihole + uptime-kuma both Up
sudo wg show                                    # wg0 up, peers listed
sudo ufw status verbose                         # 51820/udp Anywhere; all else 192.168.0.0/16
tc qdisc show dev enp1s0                        # 'cake bandwidth 90Mbit'
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # high
```

---

## Further reading

- **SETUP.md** — full step-by-step reproduction on a fresh Ubuntu 24.04 install
- **network-context.md** — deep rationale for non-obvious decisions: Docker bridge
  networking, UFW/WireGuard forwarding failure analysis, CAKE bufferbloat scope,
  WireGuard peer onboarding mistakes, Uptime Kuma monitor stack design
