# Network Context

Documents the router and Pi-hole DNS configuration that the t630 stack depends on.
This is not reproduced by SETUP.md — it describes the surrounding network environment.

## Router topology

Two routers are present. The Netgear R7000 is the main router (handles all
routing, NAT, DHCP, and the WAN connection). A secondary TP-Link router is
demoted to Access Point (AP) mode — it provides Wi-Fi coverage in areas the
Netgear doesn't reach but does not route traffic.

| Device | Role | IP |
| ------ | ---- | -- |
| Netgear R7000 | Main router (routing, NAT, DHCP) | 192.168.1.1 |
| TP-Link (TPLINK90) | Wi-Fi AP only (no routing) | 192.168.1.2 (LAN) |
| t630 thin client | DNS + VPN server | 192.168.1.118 |

### Why this split

The TP-Link has a stronger RF radio than the Netgear but a weaker CPU. Under
sustained 4K streaming load (15–25 Mbps continuous per stream) the TP-Link's
CPU saturates, heats up, and produces 60–85% packet loss — catastrophic for
everything on the network, not just the streaming device.

Root cause confirmed by testing: direct wired connection to the Netgear showed
0% loss and good speeds; connecting through the TP-Link showed loss even after
a fresh reboot. Symptom: fine ping under idle, packet loss explodes under load
(download ping spikes to 2000–4000ms, jitter >100ms).

Fix: promote the Netgear to main router (all routing, all DHCP, port forwarding
for WireGuard), demote the TP-Link to AP mode (radio only, LAN port connected
to Netgear). Now: Netgear's healthy CPU processes all packets; TP-Link's good
radio handles Wi-Fi coverage. Neither is overloaded doing the other's job.

**AP mode setup on the TP-Link:**
- Connect LAN port (not WAN) to Netgear via ethernet
- Disable DHCP server on TP-Link
- Set TP-Link LAN IP to a static address on the Netgear's subnet (e.g. 192.168.1.2)
- Disable firewall/NAT functions if the model supports it
- Give it the same SSID as the Netgear if seamless roaming is wanted

### Diagnosing future packet loss

Three-hop test to locate the failure:

```bash
# 1. Direct to gateway — is the LAN/router healthy?
ping -c 50 192.168.1.1

# 2. External IP — is WAN routing working?
ping -c 50 1.1.1.1

# 3. Domain — is DNS working?
ping -c 50 google.com
```

| Result | Meaning |
| ------ | ------- |
| #1 bad | LAN issue (router, ethernet, switch) |
| #1 ok, #2 bad | WAN/ISP issue |
| #1 ok, #2 ok, #3 bad | DNS issue (Pi-hole, Unbound) |

For ISP-side diagnosis: `mtr -rwzc 500 1.1.1.1` shows per-hop loss across
the full path. Check modem signal levels (usually `http://192.168.100.1`) —
downstream power should be −7 to +7 dBmV, SNR above 35 dB. Out-of-spec
signal levels require an ISP technician.

---

## Router: Netgear R7000 (192.168.1.1)

### DHCP reservation

The t630 has no static IP configured at the OS level. Its address is fixed via a
DHCP reservation on the router:

| Device | IP | MAC |
| ------ | -- | --- |
| t630 thin client | 192.168.1.118 | `<T630-MAC>` |

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

### Uptime Kuma monitors

Full monitor stack, with rationale for each layer:

| Monitor | Type | Target | Port | Why |
| ------- | ---- | ------ | ---- | --- |
| Unbound – Basic | DNS | `cloudflare.com` via `127.0.0.1` | 5335 | Confirms Unbound is answering queries |
| Unbound – DNSSEC | DNS | `internetsociety.org` via `127.0.0.1` | 5335 | Confirms DNSSEC validation is active (DNSSEC-signed domain) |
| Pi-hole – Full Chain | DNS | `cloudflare.com` via `127.0.0.1` | 53 | Tests entire chain: Pi-hole → Unbound → recursion |
| Pi-hole – Web UI | TCP Port | `192.168.1.118` | 8080 | Confirms Pi-hole admin panel is reachable |
| Home Router | HTTP | `http://192.168.1.1` | — | Confirms gateway is up |
| Packet Loss – Router | Push | (script pushes) | — | LAN packet loss %; `status=down` above threshold |
| Packet Loss – Internet | Push | (script pushes) | — | WAN packet loss %; distinguishes LAN vs ISP problems |

**Diagnostic logic:** if Pi-hole Full Chain goes red but Unbound Basic stays
green, the break is specifically in the Pi-hole → Unbound link, not Unbound
itself. If both go red, Unbound is the problem. Layered monitoring isolates the
failure to one component.

**Resolver field gotcha:** in Uptime Kuma's DNS monitor, the Resolver Server
field takes an IP address only — no port. Port goes in the separate Port field.
Entering `127.0.0.1:5335` in the resolver field creates an invalid double-port
and causes intermittent failures.

**Packet loss monitors:** driven by `scripts/packet-loss-monitor.sh`, which
runs via cron every 60 seconds. The loss % is placed in the `ping` field so
Uptime Kuma graphs it as a time series. Threshold: 15% while the TP-Link
situation was being resolved; lower to 5% once hardware is stable.

---

## WireGuard VPN

The t630 runs a WireGuard server that tunnels the phone back to the home network
from anywhere on cellular or untrusted Wi-Fi.

### Topology

```
iPhone (cellular or any Wi-Fi)
  │  WireGuard tunnel (UDP 51820)
  ▼
t630 wg0 interface — 10.8.0.1/24
  │  NAT / IP forward → enp1s0
  ▼
ISP WAN (<WAN-IP>) → internet
```

DNS for tunnel clients points to `10.8.0.1` (the wg0 interface), which is
reachable because Pi-hole binds to `0.0.0.0:53` via Docker port mapping. All
phone DNS therefore flows through Pi-hole + Unbound — ad-blocking and DNSSEC
validation work on cellular identically to LAN.

### Server config: wireguard/wg0.conf

| Parameter | Value |
| --------- | ----- |
| Interface address | `10.8.0.1/24` |
| ListenPort | `51820` |
| Phone peer AllowedIPs | `10.8.0.2/32` |

PostUp/PreDown manage only the MASQUERADE (nat table). FORWARD rules are not
in wg0.conf — UFW handles forwarding via `ufw default allow routed` in setup.sh.
See "UFW + WireGuard forwarding" below for why raw iptables FORWARD rules here
caused a silent failure.

### IP forwarding

Required in `/etc/sysctl.conf`:
```
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
```
Apply without reboot: `sudo sysctl -p`

### Phone client (WireGuard iOS)

| Setting | Value |
| ------- | ----- |
| Endpoint | `<WAN-IP>:51820` |
| DNS | `10.8.0.1` |
| AllowedIPs | `0.0.0.0/0, ::/0` (full tunnel) |
| On-Demand | Cellular + Wi-Fi, no SSID exclusions |

No SSID exclusions — the tunnel stays on even at home. The home-Wi-Fi loop
(phone → wg0 → enp1s0 → router → back) adds negligible latency for browsing
and avoids the operational complexity of per-SSID rules.

### Why port 51820 is open to Anywhere

Every other service in `ufw/setup.sh` is restricted to `192.168.0.0/16`.
WireGuard is the single exception: the phone connects from cellular, which is
a public IP outside the LAN. The port must be reachable from the internet for
the handshake to complete.

### Verified behavior

- Transfer counters in the WireGuard iOS app increment during browsing → tunnel
  is carrying traffic, not just "connected"
- Speed on cellular through tunnel: ~185 Mbps down / 92 Mbps up, 15 ms ping
  (ISP 2:1 down/up ratio, vs. the 10:1 ratio of 6 months prior)
- dnsleaktest.com from phone on cellular (VPN on) shows the home WAN IP —
  correct, because the phone exits through the home connection, not a
  third-party VPN provider

### Does the router need a DHCP or DNS reservation for WireGuard peers?

No. The router has no role in WireGuard addressing. Peer IPs (10.8.0.x) are
assigned by the WireGuard server via `AllowedIPs` in wg0.conf — the router
never sees the 10.8.0.0/24 subnet at all. Do not create a DHCP reservation for
VPN peers.

---

## WireGuard: UFW forwarding — what went wrong and why

### The failure

When a second peer (a Mac) was added, their internet stopped working after
connecting. The tunnel handshaked successfully and `ping 10.8.0.1` worked, but
`ping 1.1.1.1` failed — traffic was entering the tunnel but not getting out to
the internet.

### Root cause

`wg0.conf` had PostUp lines that added raw iptables FORWARD rules:
```
iptables -A FORWARD -i wg0 -o enp1s0 -j ACCEPT
iptables -A FORWARD -i enp1s0 -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

UFW owns the filter FORWARD chain. When `ufw default deny routed` is set,
UFW inserts a DROP rule at the top of the FORWARD chain. Manually appended
`-A FORWARD` rules land after UFW's DROP, so they are never reached. The
FORWARD chain policy was effectively DROP regardless of the PostUp rules.

`sudo iptables -L FORWARD -v` confirmed: policy DROP, 0 bytes matched by the
ACCEPT rules.

### The fix

Two changes — both required:

1. **Remove FORWARD rules from wg0.conf PostUp.** UFW should own forwarding,
   not raw iptables added by WireGuard.

2. **Change `ufw default deny routed` to `ufw default allow routed`** in
   `ufw/setup.sh`. This sets `DEFAULT_FORWARD_POLICY=ACCEPT`, which allows all
   forwarding through the t630. Combined with the existing LAN firewall
   restrictions on incoming ports, this is safe: the t630 is not a public
   router, and the only forwarded traffic will be from WireGuard peers that
   authenticated with a valid private key.

MASQUERADE stays in PostUp — UFW does not manage the nat table, so PostUp
is the correct and only place for it.

---

## WireGuard peer onboarding — what not to do

Lessons from adding a Mac as a second peer (May 2026).

### Use the App Store app, not Homebrew

**macOS:** Install WireGuard from the **Mac App Store**. Do not use
`brew install wireguard-tools`.

The App Store version uses macOS's Network Extension framework — the proper
OS-level VPN path. It has a GUI, generates keys for you, and routes traffic
correctly. Homebrew installs `wg-quick`, a shell script that requires `sudo`,
has had routing issues on modern macOS, and does not integrate with the system
VPN stack.

**iOS:** WireGuard is already from the App Store.

### Peer config mistakes that break everything

| Mistake | Symptom | Correct value |
| ------- | ------- | ------------- |
| `DNS = 172.17.0.1:5335` | DNS fails silently; "internet doesn't work" even when routing is fine. WireGuard's DNS field is IP only — no port. Also, `172.17.0.1` is the Docker bridge gateway on the server host and is unreachable from outside. | `DNS = 10.8.0.1` |
| `Address = 10.8.0.7/24` | Client claims ownership of the entire `10.8.0.0/24` subnet on its wg0 interface; causes routing weirdness. | `Address = 10.8.0.7/32` — client owns only its own IP |
| `AllowedIPs = 10.8.0.0/24` | Split-tunnel: web traffic bypasses the VPN. Tunnel shows "connected," whatismyip.com shows real cellular IP — indistinguishable from VPN being off. | `AllowedIPs = 0.0.0.0/0, ::/0` for full tunnel |
| No `PersistentKeepalive` | Tunnel silently drops after a few minutes of idle when peer is behind NAT (home router, cellular). | `PersistentKeepalive = 25` |

### How to verify the tunnel is actually working

Do not trust "Connected" status alone. Run these in order:

```
ping 10.8.0.1        # tunnel is up (layer 3 to server wg0 interface)
ping 1.1.1.1         # NAT/forwarding is working (traffic exits to internet)
ping google.com      # DNS is working
```

Failure at each step points to a different layer. If `ping 1.1.1.1` works
but `ping google.com` fails, the tunnel and routing are fine — only DNS is
broken (check the `DNS =` line in the peer config).

### Pi-hole must accept queries from the wg0 subnet

Pi-hole's Settings → DNS must have **"Permit all origins"** checked. Without
it, Pi-hole refuses queries from `10.8.0.x` addresses (VPN peers are not on
the LAN subnet). This is safe because UFW blocks port 53 from outside
`192.168.0.0/16` and `10.8.0.0/24` — Pi-hole is not exposed to the internet
regardless of this setting.

