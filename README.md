# localDNS  
### A home network defined by its tunnel, not its hardware.

The WireGuard tunnel is the membrane. It defines what is inside and what is outside — not physical location, not which Wi-Fi network you are on. If you hold a key, you are inside. If you do not, you are outside.

Everything else in the stack serves that gradient:

- **Pi‑hole** — filters DNS at the edge; blocks telemetry before it reaches any device  
- **Unbound** — recursive DNS with DNSSEC; no third-party resolver ever sees your queries  
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
- recursive resolution with DNSSEC (Unbound — no third-party resolver in the chain)
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
┌──────────────────────────────┐
│ UNBOUND RECURSIVE DNS CORE   │ ──(DNSSEC)──> [ Internet Root ]
└──────────────────────────────┘
```
Dropping a domain at DNS eliminates the request entirely — no payload, no parsing, no CPU cost, no battery drain on the client.

---

## DNS execution layers

| Component | Execution layer | Rationale |
| --------- | --------------- | --------- |
| Pi‑hole | Docker container | Isolates blocklist ingestion, gravity updates, and UI |
| Unbound | Native Linux service | No bridge overhead; DNSSEC validation closest to the wire |

Pi-hole sends upstream queries to Unbound at `172.17.0.1#5335` (the Docker bridge gateway to the host). No third-party resolver is ever in the chain.

---

## Hardening

- UFW restricted to RFC1918 and the WireGuard subnet (`10.8.0.0/24`)
- WireGuard port 51820/UDP is the only WAN-exposed service
- CPU governor locked to performance mode
- AMD GPU forced into high-performance mode (headless downclocking prevention)
- Uptime Kuma monitors every layer: Unbound, Pi-hole, DNS chain, router, packet loss
- Automated Unbound cache dumps and restores across reboots

---

## Remote access

LAN and WG subnet only:

- NoMachine (port 4000)
- xrdp (port 3389)
- SSH (port 22)

No cloud. No WAN exposure. SSH is also reachable from WireGuard peers via `ssh user@10.8.0.1`.

---

## Repository contents

| Path | Purpose |
|------|---------|
| `wireguard/wg0.conf` | WireGuard server config — interface, peers, MASQUERADE |
| `wireguard/peer-template.conf` | Reference config for adding a new peer |
| `pihole/docker-compose.yml` | Pi-hole container |
| `uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring stack |
| `unbound/server.conf` | Unbound interfaces, ACLs, ports, security flags, DNSSEC trust anchor |
| `unbound/tuning.conf` | Cache sizes, TTL policy, threading — single source of truth |
| `unbound/remote-control.conf` | Unix socket for `unbound-control` |
| `scripts/unbound-cache-dump` | Dumps Unbound cache to disk |
| `scripts/unbound-cache-load` | Restores cache at startup |
| `systemd/unbound.service.d/override.conf` | Hooks cache load/dump into service lifecycle |
| `systemd/unbound-cache-dump.timer` | Hourly cache backup timer |
| `systemd/unbound-cache-dump.service` | One-shot cache backup worker |
| `systemd/gpu-performance.service` | AMD GPU high-performance mode at boot |
| `systemd/cpu-performance.service` | CPU governor locked to performance |
| `udev/99-amdgpu-performance.rules` | Re-asserts GPU profile on DRM events |
| `ufw/setup.sh` | Firewall rules — LAN + WG subnet, WireGuard WAN port |
| `cake/setup.sh` | CAKE QoS setup script |
| `systemd/cake.service` | CAKE systemd service |
| `nomachine/server.cfg` | NoMachine remote desktop config |
| `scripts/packet-loss-monitor.sh` | Cron-driven packet loss monitor feeding Uptime Kuma |
| `scripts/cake-monitor.sh` | Cron-driven CAKE qdisc health monitor feeding Uptime Kuma |

---

## Deployment

See:

- **SETUP.md** — provisioning, configuration, kernel tuning
- **network-context.md** — topology, addressing, firewalling, WireGuard runbooks
- **CLAUDE.md** — structural guidelines

