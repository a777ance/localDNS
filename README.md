# localDNS
Self-hosted recursive DNS wit Pi-hole and Unbound on Ubuntu, running on an HP t630 thin client

# localDNS

Self-hosted recursive DNS for a small home and small-business network. Pi-hole handles ad/tracker blocking and acts as the LAN's DNS server; Unbound runs alongside as a recursive resolver so queries go directly to root and authoritative servers instead of an upstream provider. Runs on an HP t630 thin client under Ubuntu 24.04 LTS.

## Why

Off-the-shelf DNS (ISP resolver, public 8.8.8.8 / 1.1.1.1) means a third party sees every name your network looks up. Pointing Pi-hole at a local Unbound instance instead of an external resolver removes that observation point. Blocklists handle ads and trackers at the network edge so every device benefits without per-device configuration.

## Architecture

[ LAN clients ]
│  port 53
▼
[ Pi-hole (Docker) ]──── blocklists, query logging, web UI :8080
│  port 5335
▼
[ Unbound (host) ]────── recursive resolution, DNSSEC validation
│
▼
[ Root + authoritative DNS servers ]

Pi-hole runs in a Docker container with named volumes for persistent configuration. It forwards non-blocked queries to Unbound, which performs full recursive resolution from the root servers, caches results, and validates DNSSEC signatures.

## Hardware

- HP t630 thin client (AMD Carrizo APU, 4 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS
- Wired Gigabit Ethernet

## Repository contents

| Path | Purpose |
|------|---------|
| `pihole/docker-compose.yml` | Pi-hole container definition with named volumes and Unbound upstream |
| `unbound/` | Unbound configuration drop-ins: tuning, performance, DNSSEC, remote control |
| `systemd/gpu-performance.service` | Forces AMD GPU to high-performance state at boot (see Notes) |
| `udev/99-amdgpu-performance.rules` | Re-asserts GPU performance level on driver events |

## Reproduction

Assumes a clean Ubuntu 24.04 install on the target host.

```bash
# Install Unbound
sudo apt update
sudo apt install -y unbound

# Drop in configuration
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo systemctl restart unbound

# Install Docker, then bring up Pi-hole
cd pihole
cp docker-compose.yml.example docker-compose.yml  # then set WEBPASSWORD
docker compose up -d
```

Point your router's DHCP DNS option at the t630's IP. Done.

## Notes

### Carrizo headless GPU throttling

The AMD Carrizo APU in the t630 aggressively downclocks its iGPU when no display is detected, which crippled NoMachine remote desktop performance. Three-part remediation:

1. **Kernel parameters** in `/etc/default/grub`: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. **systemd service** writes `high` to `power_dpm_force_performance_level` at boot
3. **udev rule** re-asserts `high` on `add|change` events to the DRM subsystem, catching display hotplug and runtime PM transitions that would otherwise re-throttle the GPU

The udev rule is what actually keeps the fix stable across a session — the service alone fires once and isn't re-triggered when the kernel re-evaluates power state later.

### Secrets

`WEBPASSWORD` in the compose file is a placeholder. Set it to a real value at deployment, or pass via `.env` file (gitignored). The Unbound configs do not contain keys; `remote-control.conf` references stock paths that Unbound creates locally with `unbound-control-setup`.

## License

MIT
