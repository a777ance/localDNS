# localDNS  
### A home network defined by its tunnel, not its hardware.

The WireGuard tunnel is the membrane. It defines what is inside and what is outside — not physical location, not which Wi-Fi network you are on. If you hold a key, you are inside. If you do not, you are outside.

Everything else in the stack serves that gradient:

- **Pi‑hole** — filters DNS at the edge; blocks telemetry before it reaches any device  
- **Unbound** — the DNS decision point: personal queries resolve recursively with DNSSEC (no third party ever sees them); high‑volume streaming domains are forwarded to Cloudflare over DNS‑over‑TLS (encrypted from the ISP) for speed  
- **Thin client (t630)** — dedicated compute for the membrane; always on, low power  
- **UFW** — explicit firewall; LAN and WG subnet only, no WAN exposure  
- **Uptime Kuma** — monitors every layer of the stack  
- **CAKE QoS** — shapes VPN client traffic; prevents any one peer from saturating the pipe  

No cloud dependencies. No bundled telemetry. No hidden behavior.

The gradient is maintained by cryptographic identity. Physical location is irrelevant.

---

## The Membrane

The tunnel is the membrane. It maintains a gradient between trusted inside and untrusted outside.

Peers inside the tunnel get:
- filtered DNS (Pi-hole blocks telemetry and tracking domains before they resolve)
- private recursive resolution with DNSSEC for personal traffic (Unbound — no third-party resolver in the chain); streaming domains forwarded to Cloudflare over DNS-over-TLS (encrypted from the ISP) for speed
- shaped egress (CAKE — fair queuing, no single peer saturates the pipe)

This works identically whether the peer is on the home LAN or on cellular halfway across the world. Physical location does not change what is inside.

---

## Zero‑Byte Drop Framework

Dropping unwanted domains at DNS means:

- no request  
- no payload  
- no parsing  
- no CPU cost  
- no battery drain  

```text
[ Web Request ]
      │
      ▼
┌───────────────┐     Blocked      ┌───────────────────────────────┐
│  MEMBRANE     │ ───────────────> │ 0.0.0.0 (Zero-byte Drop)      │
│ (Pi-hole Edge)│                  │ - No JS parsed by client      │
└───────────────┘                  │ - Zero CPU / battery overhead │
      │                            └───────────────────────────────┘
  Allowed
      │
      ▼
┌──────────────────────────────┐  personal / sensitive
│ UNBOUND — single decision pt │ ──(DNSSEC, recursive)──> [ Internet Root ]
│                              │  streaming / low-sensitivity
│                              │ ──(DNS-over-TLS, :853)──> [ Cloudflare 1.1.1.1 / 1.0.0.1 ]
└──────────────────────────────┘
```
Dropping a domain at DNS eliminates the request entirely — no payload, no parsing, no CPU cost, no battery drain on the client. Allowed queries reach Unbound, which keeps personal lookups recursive and private while forwarding streaming domains to Cloudflare over DNS-over-TLS (encrypted from the ISP) for speed.

---

## DNS execution layers

| Component | Execution layer | Rationale |
| --------- | --------------- | --------- |
| Pi‑hole | Docker container | Isolates blocklist ingestion, gravity updates, and UI |
| Unbound | Native Linux service | No bridge overhead; DNSSEC validation closest to the wire |

Pi-hole sends every upstream query to Unbound at `172.17.0.1#5335` (the Docker bridge gateway to the host) — it does no resolver selection itself. Unbound is the single decision point: personal and sensitive domains resolve recursively with no third-party resolver in the chain, while high-volume streaming domains are forwarded to **Cloudflare over DNS-over-TLS** (`1.1.1.1@853` / `1.0.0.1@853`, `forward-tls-upstream`), encrypting the forward-path from the ISP. The split lives entirely in `unbound/streaming-forward.conf`. The recursive nucleus is never forwarded — that invariant is what keeps sensitive lookups off Cloudflare.

---

## Hardening

- UFW restricted to RFC1918 and the WireGuard subnet (`10.8.0.0/24`)
- WireGuard port 51820/UDP is the only WAN-exposed service
- CPU governor locked to performance mode
- AMD GPU forced into high-performance mode (headless downclocking prevention)
- Uptime Kuma monitors every layer: Unbound, Pi-hole, DNS chain, router, packet loss, CAKE qdisc
- Automated Unbound cache dumps and restores across reboots

---

## Remote access

LAN and WG subnet only:

- NoMachine (port 4000)
- xrdp (port 3389)
- SSH (port 22)

No cloud. No WAN exposure. SSH is also reachable from WireGuard peers via `ssh user@10.8.0.1`.

---

## Repository layout

Folders are numbered by installation order. See SETUP.md for the full walkthrough.

| Step | Path | Purpose |
|------|------|---------|
| 1 | `01-unbound/server.conf` | Unbound interfaces, ACLs, ports, security flags |
| 1 | `01-unbound/tuning.conf` | Cache sizes, TTL policy, threading — single source of truth |
| 1 | `01-unbound/streaming-forward.conf` | Domain split: streaming → Cloudflare DoT (`1.1.1.1@853`), all else → recursive |
| 1 | `01-unbound/remote-control.conf` | Unix socket for `unbound-control` |
| 1 | `01-unbound/root-auto-trust-anchor-file.conf` | DNSSEC trust anchor |
| 1 | `01-unbound/unbound-cache-dump` | Dumps Unbound cache to disk |
| 1 | `01-unbound/unbound-cache-load` | Restores cache at startup |
| 1 | `01-unbound/unbound-cache-dump.timer` | Hourly cache backup timer |
| 1 | `01-unbound/unbound-cache-dump.service` | One-shot cache backup worker |
| 1 | `01-unbound/unbound.service.d/override.conf` | Hooks cache load/dump into service lifecycle |
| 2 | *(Docker CE — no config files, install only)* | |
| 3 | `02-pihole/docker-compose.yml` | Pi-hole container |
| 4 | `03-host-dns/host-dns.conf` | Host resolver fix — points t630's own DNS at external resolvers after Pi-hole takes port 53 |
| 5 | `04-ufw/setup.sh` | Firewall rules — LAN + WG subnet, WireGuard WAN port |
| 6 | `05-wireguard/wg0.conf` | WireGuard server config — interface, peers, MASQUERADE |
| 6 | `05-wireguard/peer-template.conf` | Reference config for adding a new peer |
| 7 | `06-cake/setup.sh` | CAKE QoS setup script |
| 7 | `06-cake/cake.service` | CAKE systemd service |
| 8 | `07-uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring stack |
| 8 | `07-uptime-kuma/packet-loss-monitor.sh` | Cron-driven packet loss monitor feeding Uptime Kuma |
| 8 | `07-uptime-kuma/cake-monitor.sh` | Cron-driven CAKE qdisc health monitor feeding Uptime Kuma |
| 9 | `08-gpu-performance/gpu-performance.service` | AMD GPU high-performance mode at boot |
| 9 | `08-gpu-performance/cpu-performance.service` | CPU governor locked to performance |
| 9 | `08-gpu-performance/99-amdgpu-performance.rules` | Re-asserts GPU profile on DRM events |
| 10 | `09-remote-desktop/server.cfg` | NoMachine remote desktop config |

---

## Deployment

See:

- **SETUP.md** — provisioning, configuration, kernel tuning
- **network-context.md** — topology, addressing, firewalling, WireGuard runbooks
- **CLAUDE.md** — structural guidelines

