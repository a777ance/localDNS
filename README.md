# localDNS

Self-hosted recursive DNS with Pi-hole and Unbound on Ubuntu, running on an HP t630 thin client.

## What it does

LAN clients send DNS queries to Pi-hole, which handles ad/tracker blocking and query logging. Non-blocked queries are forwarded to Unbound, which performs full recursive resolution from the root servers, validates DNSSEC signatures, and caches results. No upstream DNS provider — every query goes directly to authoritative servers.
[ LAN clients ]
│  port 53
▼
[ Pi-hole (Docker) ] ── blocklists, query logging, web UI :8080
│  port 5335
▼
[ Unbound (host) ] ──── recursive resolution, DNSSEC validation, cache
│
▼
[ Root + authoritative DNS servers ]
Uptime Kuma monitors the stack and other LAN services at port 3001.

## Why

Off-the-shelf DNS (ISP resolver, 8.8.8.8, 1.1.1.1) means a third party sees every name your network looks up. A local Unbound instance removes that observation point entirely. Pi-hole blocklists handle ads and trackers at the network edge so every device benefits without per-device configuration.

## Hardware

- HP t630 thin client (AMD Carrizo GX-420GI quad-core APU, 4 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Gigabit Ethernet, Wi-Fi disabled

## Repository contents

| Path | Purpose |
| ---- | ------- |
| `pihole/docker-compose.yml` | Pi-hole container with named volumes and Unbound upstream |
| `uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring container |
| `unbound/server.conf` | Interface, port, access control, security hardening |
| `unbound/tuning.conf` | Cache sizes, threads, TTL policy, serve-expired |
| `unbound/remote-control.conf` | Unix socket for unbound-control |
| `unbound/root-auto-trust-anchor-file.conf` | DNSSEC trust anchor path |
| `scripts/unbound-cache-dump` | Atomically writes Unbound cache to disk |
| `scripts/unbound-cache-load` | Restores cache dump into Unbound at start |
| `systemd/unbound.service.d/override.conf` | Hooks cache load/dump into Unbound start/stop |
| `systemd/unbound-cache-dump.timer` | Triggers hourly cache dump, 10 min after boot |
| `systemd/unbound-cache-dump.service` | One-shot service called by the timer |
| `systemd/gpu-performance.service` | Forces AMD GPU to high-performance state at boot |
| `systemd/cpu-performance.service` | Forces CPU governor to performance at boot |
| `udev/99-amdgpu-performance.rules` | Re-asserts GPU performance level on DRM events |
| `ufw/setup.sh` | Firewall rules — all services restricted to LAN |
| `nomachine/server.cfg` | NoMachine server configuration |

## Reproduction

See [SETUP.md](SETUP.md) for the full walkthrough.

Quick reference:

```bash
# Unbound
sudo apt install -y unbound
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo cp scripts/unbound-cache-{dump,load} /usr/local/bin/
sudo chmod +x /usr/local/bin/unbound-cache-{dump,load}
sudo mkdir -p /etc/systemd/system/unbound.service.d
sudo cp systemd/unbound.service.d/override.conf /etc/systemd/system/unbound.service.d/
sudo cp systemd/unbound-cache-dump.{timer,service} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unbound unbound-cache-dump.timer

# Docker CE — see SETUP.md Part 2 for repo setup
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Pi-hole
cd pihole && docker compose up -d

# Uptime Kuma
mkdir -p ~/uptime-kuma
cp uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d

# Firewall
sudo bash ufw/setup.sh

# GPU remediation (Carrizo-specific)
sudo cp systemd/gpu-performance.service systemd/cpu-performance.service /etc/systemd/system/
sudo cp udev/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance cpu-performance
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```

## Known issues

- **Pi-hole upstream DNS.** `PIHOLE_DNS_=127.0.0.1#5335` came off the running container and works in production. The architecturally correct value for Docker bridge networking is `172.17.0.1#5335`. Under investigation.
- **WEBPASSWORD inline.** Set as `CHANGE_ME` in the compose file. Moving to a gitignored `.env` is planned.
- **Root hints freshness.** `/var/lib/unbound/root.hints` is not auto-updated; refresh manually when needed: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root`

## Remote desktop

Three remote access methods are installed for administering the t630:

- **NoMachine** (port 4000) — primary, NX protocol, best performance
- **xrdp** (port 3389) — RDP fallback for Windows native clients
- **x2goserver** — alternative for low-bandwidth connections

All restricted to LAN via UFW.

## Notes: Carrizo headless GPU throttling

The AMD Carrizo APU aggressively downclocks its iGPU with no display attached, crippling NoMachine performance. Four-part fix:

1. **GRUB** — `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. **gpu-performance.service** — writes `high` to `power_dpm_force_performance_level` at boot
3. **cpu-performance.service** — sets all cores to `performance` governor at boot
4. **udev rule** — re-asserts GPU level on every DRM event (the critical re-trigger)

## License

MIT
