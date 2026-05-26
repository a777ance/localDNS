# Network Context

Documents the router and Pi-hole DNS configuration that the t630 stack depends on.
This is not reproduced by SETUP.md — it describes the surrounding network environment.

## Router: Netgear R7000 (192.168.1.1)

### DHCP reservation

The t630 has no static IP configured at the OS level. Its address is fixed via a
DHCP reservation on the router:

| Device | IP | MAC |
| ------ | -- | --- |
| t630 thin client | 192.168.1.118 | 7C:D3:0A:77:93:AE |

This means the t630 always gets the same address without needing to manage a static
IP in netplan or NetworkManager. If the t630 is ever rebuilt, the reservation keeps
its address stable automatically.

### DNS pushed to LAN clients

Under Basic → Internet Setup, the router is configured with:

- Primary DNS: `192.168.1.118` (Pi-hole on the t630)
- Secondary DNS: `1.1.1.1` (Cloudflare fallback)

The Netgear R7000 advertises these same DNS servers to DHCP clients, so every device
on the LAN sends DNS queries directly to Pi-hole rather than through a router proxy.
This means Pi-hole sees individual client IPs in its query log, enabling per-device
statistics and filtering.

**Secondary DNS tradeoff:** The `1.1.1.1` fallback is intentional. If the t630 goes
down, the network stays online. The cost is that ad-blocking and local DNS resolution
stop working until the t630 is back. For a home network this is the right tradeoff.
Removing the fallback would make the entire network go offline when the t630 reboots.

### Router's own DNS

The router also uses Pi-hole for its own lookups (visible in Advanced Home →
Internet Port → Domain Name Server). This means the router's own queries are
filtered too.

### WAN security settings (Advanced → WAN Setup)

| Setting | Value | Why |
| ------- | ----- | --- |
| NAT Filtering | Secured | Blocks unsolicited inbound packets |
| Disable SIP ALG | Yes | SIP ALG causes VoIP problems; disabled by default |
| Respond to ping on WAN | No | Reduces attack surface |
| Port scan / DoS protection | Enabled | Router-level rate limiting |
| DMZ | Disabled | Nothing exposed to internet directly |

---

## Pi-hole DNS settings (Settings → DNS)

### Why 172.17.0.1#5335 — not 127.0.0.1#5335

Pi-hole runs inside a Docker container. Inside the container, `127.0.0.1` is the
container's own loopback — not the host. Unbound runs on the host OS. To reach it,
Pi-hole must use the Docker bridge gateway IP, which is `172.17.0.1` — the host's
address as seen from inside the container.

The `PIHOLE_DNS_` value in `pihole/docker-compose.yml` is `127.0.0.1#5335`. This is
what Pi-hole receives on first container creation. After first run, Pi-hole stores
the upstream DNS in its persistent database (in the `pihole_data` Docker volume).
The UI-configured value (`172.17.0.1#5335`) then takes precedence over the compose
env var. The compose file value only matters when deploying to a completely fresh
volume.

**On a fresh deployment:** after running `docker compose up -d`, go to
Settings → DNS, clear `127.0.0.1#5335` from the custom upstream field, enter
`172.17.0.1#5335`, and click Save & Apply. This persists in the volume across
container restarts.

### Why "Permit all origins" is checked

Pi-hole flags this as "potentially dangerous." It is safe here because UFW restricts
port 53 to `192.168.0.0/16`. No query from outside the LAN can reach Pi-hole
regardless of this setting. "Allow only local requests" would also work but would
block queries from Docker containers and other non-directly-attached interfaces.
"Permit all origins" is the correct setting when the firewall handles the boundary.

### No preset upstream servers checked

None of the preset upstream servers (Google, Cloudflare, Quad9, etc.) are enabled.
All upstream resolution goes through the custom entry (`172.17.0.
1#5335`), which
routes to Unbound on the host. This is the whole point — no third-party resolver
ever sees the query.
| NAT Filtering | Secured | Blocks unsolicited inbound packets |
| Disable SIP ALG | Yes | SIP ALG causes VoIP problems; disabled by default |

________________

Uptime Kuma — Monitoring

Uptime Kuma runs in Docker on port 3001 and monitors Unbound via a DNS monitor 
querying 127.0.0.1:5335.

WHY network_mode: host — NOT A BRIDGE NETWORK

Uptime Kuma's docker-compose.yml uses network_mode: host, which removes Docker's 
network isolation and places the container directly on the host network stack. This 
is required because Ubuntu 22.04 uses nftables as its firewall backend. Legacy 
iptables rules don't affect the active ruleset, and the INPUT chain has a default 
DROP policy. As a result, Docker bridge IPs (172.17.0.1, 172.18.0.1) are not 
reachable from host processes or other containers on arbitrary ports like 5335 — 
even with explicit UFW allow rules added.

With network_mode: host, Uptime Kuma shares the host network stack and reaches 
Unbound at 127.0.0.1:5335 directly, the same way any native host process would.

Consequence: the ports: mapping is removed from the compose file. Uptime Kuma 
remains available at port 3001 — it binds directly on the host interface rather 
than through Docker's port mapping layer.

Monitor configuration (Uptime Kuma → Edit Monitor):
  Type:            DNS
  Hostname:        google.com
  Resolver Server: 127.0.0.1
  Port:            5335
  Record Type:     A

