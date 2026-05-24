# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project posture

Working-state snapshot of a self-hosted DNS and monitoring stack on an HP t630. Two purposes: portfolio artifact and rollback target.

**The live t630 is the source of truth.** Nothing here affects the running system until manually deployed:

- Unbound: `sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/ && sudo systemctl restart unbound`
- Pi-hole: `cd pihole && docker compose up -d`
- Uptime Kuma: `cd ~/uptime-kuma && docker compose up -d`
- UFW: `sudo bash ufw/setup.sh`
- NoMachine: `sudo cp nomachine/server.cfg /usr/NX/etc/server.cfg && sudo /usr/NX/bin/nxserver --restart`

## Working philosophy

Move toward truth, goodness, and elegance. Welcome clarity and correctness. Reject churn.

- Every commit to `main` must leave SETUP.md able to reproduce a working system on clean Ubuntu 24.04.
- Use feature branches for half-finished work.

## Load-bearing known issues

| Issue | Status |
| ----- | ------ |
| `PIHOLE_DNS_=127.0.0.1#5335` | Works in production. Do not change without verifying live Pi-hole upstream. |
| `WEBPASSWORD` inline | Placeholder only. Do not commit real credentials. |

## Unbound config structure

Four drop-ins, loaded alphabetically:

- `server.conf` — interface, port, access control, hardening
- `tuning.conf` — **single source of truth** for all performance/caching values
- `remote-control.conf` — Unix socket
- `root-auto-trust-anchor-file.conf` — DNSSEC anchor

Do not reintroduce `performance.conf` or `ttl-override.conf`. They were consolidated into `tuning.conf`.

## Firewall

All services are LAN-only (`192.168.0.0/16`). `ufw/setup.sh` is canonical. Do not open any port to Anywhere.

## AMD Carrizo remediation

Four load-bearing pieces — all required:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `systemd/gpu-performance.service`
3. `systemd/cpu-performance.service`
4. `udev/99-amdgpu-performance.rules` — the critical re-trigger on DRM events

## Verification

```bash
unbound-checkconf
dig @127.0.0.1 -p 5335 example.com +dnssec
docker compose -f pihole/docker-compose.yml config
docker ps
cat /sys/class/drm/card*/device/power_dpm_force_performance_level
sudo ufw status verbose
```
