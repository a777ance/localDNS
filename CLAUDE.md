# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project posture

Working-state snapshot of a self-hosted DNS and monitoring stack on an HP t630.
Two purposes: portfolio artifact and rollback target.

**The live t630 is the source of truth.** Edits here do not affect the running
system until manually deployed:

- Unbound: `sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/ && sudo systemctl restart unbound`
- Pi-hole: `cd pihole && docker compose up -d`
- Uptime Kuma: `cd ~/uptime-kuma && docker compose up -d`
- UFW: `sudo bash ufw/setup.sh`
- NoMachine: `sudo cp nomachine/server.cfg /usr/NX/etc/server.cfg && sudo /usr/NX/bin/nxserver --restart`
- WireGuard: `sudo cp wireguard/wg0.conf /etc/wireguard/wg0.conf && sudo systemctl restart wg-quick@wg0`

## Working philosophy

Move toward truth, goodness, and elegance. Welcome clarity and correctness. Reject churn.
Every commit to `main` must leave SETUP.md able to reproduce a working system on
clean Ubuntu 24.04. Use feature branches for half-finished work.

## Load-bearing known issues

| Issue | Status |
| ----- | ------ |
| `PIHOLE_DNS_=127.0.0.1#5335` in compose | Initial value only. UI must be updated to `172.17.0.1#5335` after first deploy. See docs/network-context.md. |
| `WEBPASSWORD` inline | Placeholder only. Do not commit real credentials. |

## Unbound config structure

Four drop-ins loaded alphabetically. `tuning.conf` is the single source of truth
for all performance/caching values. Do not reintroduce `performance.conf` or
`ttl-override.conf` — they were consolidated.

## Firewall

All services LAN-only (`192.168.0.0/16`). `ufw/setup.sh` is canonical.
One intentional exception: port 51820/UDP (WireGuard) is open to Anywhere —
the phone connects from cellular, so this cannot be LAN-restricted. Everything
else remains LAN-only.

## Pi-hole upstream DNS

`172.17.0.1#5335` — Docker bridge gateway to Unbound on the host.
`127.0.0.1` does not work from inside a container. See docs/network-context.md.

## AMD Carrizo remediation

Four load-bearing pieces — all required:
1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `systemd/gpu-performance.service`
3. `systemd/cpu-performance.service`
4. `udev/99-amdgpu-performance.rules` — critical re-trigger on DRM events

## Verification

```bash
unbound-checkconf
dig @127.0.0.1 -p 5335 example.com +dnssec
docker ps
cat /sys/class/drm/card*/device/power_dpm_force_performance_level
sudo ufw status verbose
```


