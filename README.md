# localDNS

Self-hosted recursive DNS with Pi-hole and Unbound on Ubuntu, running on an HP t630 thin client.

## What it does

LAN clients send DNS queries directly to Pi-hole, which handles ad/tracker blocking
and query logging. Non-blocked queries go to Unbound, which performs full recursive
resolution from the root servers, validates DNSSEC, and caches results. No upstream
DNS provider — no 8.8.8.8, no 1.1.1.1, no ISP resolver.
[ LAN clients ]
│  port 53  (pushed via router DHCP)
▼
[ Pi-hole (Docker) ] ── blocklists, query logging, web UI :8080
│  172.17.0.1:5335  (Docker bridge → host)
▼
[ Unbound (host) ] ──── recursive resolution, DNSSEC validation, cache
│
▼
[ Root + authoritative DNS servers ]
Uptime Kuma monitors the stack and other LAN services at port 3001.

## Why

Off-the-shelf DNS means a third party sees every name your network looks up.
A local Unbound instance removes that observation point. Pi-hole blocklists handle
ads and trackers at the network edge — every device benefits without per-device
configuration.

## Hardware

- HP t630 thin client (AMD Carrizo GX-420GI quad-core, 4 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Gigabit Ethernet, static via DHCP reservation on Netgear R7000

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
| `systemd/unbound-cache-dump.timer` | Hourly cache dump, starting 10 min after boot |
| `systemd/unbound-cache-dump.service` | One-shot service called by the timer |
| `systemd/gpu-performance.service` | Forces AMD GPU to high-performance state at boot |
| `systemd/cpu-performance.service` | Forces CPU governor to performance at boot |
| `udev/99-amdgpu-performance.rules` | Re-asserts GPU performance level on DRM events |
| `ufw/setup.sh` | Firewall rules — all services restricted to LAN |
| `nomachine/server.cfg` | NoMachine server configuration |
| `docs/network-context.md` | Router config, Pi-hole DNS settings, and rationale |

## Reproduction

See [SETUP.md](SETUP.md) for the full walkthrough.

## Known issues

- **WEBPASSWORD inline.** Set as `CHANGE_ME` in `pihole/docker-compose.yml`.
  Moving to a gitignored `.env` is planned.
- **Pi-hole upstream must be set in UI after first deploy.** The compose env var
  sets `127.0.0.1#5335` on first run. Change it to `172.17.0.1#5335` in
  Settings → DNS after the container starts. See `docs/network-context.md`.
- **Root hints not auto-refreshed.** Refresh manually:
  `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root`

## Notes: Carrizo headless GPU throttling

The AMD Carrizo iGPU downclocks aggressively with no display attached, killing
NoMachine performance. Four-part fix in this repo: GRUB kernel params, GPU systemd
service, CPU systemd service, and udev rule. All four are required — the udev rule
is the critical re-trigger for DRM events after boot.

## Remote desktop

Three access methods installed: NoMachine (port 4000, primary), xrdp (port 3389,
RDP fallback), x2goserver (low-bandwidth alternative). All LAN-only via UFW.

## License

MIT

