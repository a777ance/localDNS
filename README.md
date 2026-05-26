# localDNS

Self-hosted DNS filtering and monitoring stack on an HP t630 thin client. Each service does one job and is replaceable. No cloud dependencies.

---

## Network Topology

```
                        ┌─────────────────────────────────────────┐
                        │         192.168.1.118  (t630)           │
                        │                                         │
  LAN clients ──DNS──▶  │  ┌─────────────┐   ┌───────────────┐  │
                        │  │   Pi-hole   │──▶│    Unbound    │  │
                        │  │  (Docker)   │   │  (native svc) │  │
                        │  │  :8080 UI   │   │  127.0.0.1    │  │
                        │  └─────────────┘   │    :5335      │  │
                        │        ▲           └───────┬───────┘  │
                        │   172.17.0.1               │          │
                        │  (bridge GW)               ▼          │
                        │                       Internet         │
                        │  ┌──────────────┐   (root servers,    │
                        │  │ Uptime Kuma  │    DNSSEC)          │
                        │  │  (Docker,    │                      │
                        │  │  host net)   │                      │
                        │  │  :3001 UI    │                      │
                        │  └──────────────┘                      │
                        │                                         │
                        │  NoMachine :4000  │  xrdp :3389        │
                        └─────────────────────────────────────────┘
                                    ▲
                         Netgear R7000  (192.168.1.1)
                         - DHCP reservation → 192.168.1.118
                         - DNS primary      → 192.168.1.118
                         - DNS secondary    → 1.1.1.1 (fallback)
```

---

## Services & Ports

| Service | Address | Access |
|---------|---------|--------|
| Pi-hole web UI | `http://192.168.1.118:8080/admin/` | browser |
| Uptime Kuma web UI | `http://192.168.1.118:3001` | browser |
| Unbound (DNS) | `127.0.0.1:5335` | host loopback only |
| NoMachine | `192.168.1.118:4000` | NoMachine app |
| xrdp | `192.168.1.118:3389` | RDP client |
| SSH | `192.168.1.118:22` | terminal |

All ports are LAN-only (`192.168.0.0/16`). UFW blocks everything else.

---

## DNS Query Flow

```
LAN device
    │
    │  port 53
    ▼
Pi-hole (192.168.1.118)
    │  blocklist check
    ├──▶ BLOCKED → 0.0.0.0 (no request ever leaves)
    │
    │  allowed query
    │  port 5335, via 172.17.0.1 (Docker bridge gateway)
    ▼
Unbound (127.0.0.1:5335, native Linux)
    │  recursive resolution + DNSSEC validation
    ▼
Root servers → TLD → Authoritative
```

**Why `172.17.0.1` not `127.0.0.1`:** Pi-hole runs in a Docker container. Inside the container, `127.0.0.1` is the container's own loopback. `172.17.0.1` is the Docker bridge gateway — how the container reaches the host where Unbound is running. See [network-context.md](network-context.md) for full details.

---

## Pi-hole DNS Settings (post-deploy manual step)

After first `docker compose up -d`, the upstream DNS must be set manually in the UI:

1. Go to **Settings → DNS**
2. Clear `127.0.0.1#5335` from the custom upstream field
3. Enter `172.17.0.1#5335`
4. Check **Permit all origins** (safe because UFW restricts port 53 to LAN)
5. Uncheck all preset upstream servers (Google, Cloudflare, etc.)
6. Click **Save & Apply**

---

## Repository Map

| Path | Purpose |
|------|---------|
| `pihole/docker-compose.yml` | Pi-hole container config |
| `uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring stack |
| `unbound/server.conf` | Unbound interfaces, ACLs, ports, security |
| `unbound/tuning.conf` | Threads, cache sizes, TTL policy |
| `unbound/remote-control.conf` | Local `unbound-control` socket |
| `unbound/root-auto-trust-anchor-file.conf` | DNSSEC trust anchor |
| `scripts/unbound-cache-dump` | Dumps Unbound cache to disk |
| `scripts/unbound-cache-load` | Restores cache at startup |
| `systemd/unbound.service.d/override.conf` | Hooks cache load/dump into service lifecycle |
| `systemd/unbound-cache-dump.timer` | Hourly cache backup timer |
| `systemd/gpu-performance.service` | Forces AMD GPU into high-performance mode |
| `systemd/cpu-performance.service` | Locks CPU governor to performance mode |
| `udev/99-amdgpu-performance.rules` | Reasserts GPU profile on DRM/hotplug events |
| `ufw/setup.sh` | LAN-only firewall (RFC1918 restricted) |
| `nomachine/server.cfg` | NoMachine remote desktop config |
| `network-context.md` | Router config, DNS topology, addressing detail |
| `SETUP.md` | Full provisioning guide for clean Ubuntu 24.04 |

---

## Deployment

```bash
# Unbound
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo systemctl restart unbound
unbound-checkconf
dig @127.0.0.1 -p 5335 example.com +dnssec

# Pi-hole
cd pihole && docker compose up -d
# then set upstream DNS in UI (see above)

# Uptime Kuma
cd ~/uptime-kuma && docker compose up -d

# Firewall
sudo bash ufw/setup.sh
sudo ufw status verbose
```
