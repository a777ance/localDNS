# Network Context

Documents the router and DNS/VPN configuration that the t630 stack depends on.
This is not reproduced by SETUP.md — it describes the surrounding network environment.

## Router topology

The Netgear R7000 is the sole router (routing, NAT, DHCP, WAN). The t630 is the
DNS and VPN server, hanging off the LAN.

| Device | Role | IP |
| ------ | ---- | -- |
| Netgear R7000 | Router (routing, NAT, DHCP) | 192.168.1.1 |
| t630 thin client | DNS + VPN server | 192.168.1.118 |

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
down, the network stays online. The cost is twofold: ad-blocking and DNSSEC stop
working, and DNS queries are concentrated at Cloudflare rather than diluted across
the recursive resolver graph. Some OS DNS clients will also fall back to the secondary
during transient slowness (blocklist updates, high load) — not only on full t630
failure — so `1.1.1.1` receives some queries even when the stack is healthy.
Removing the fallback would make the entire network go offline when the t630 reboots,
which is the wrong tradeoff for a home network.

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

The `PIHOLE_DNS_` value in `pihole/docker-compose.yml` is `172.17.0.1#5335`. On
fresh-volume creation, Pi-hole reads this env var to seed its upstream DNS database.
After first run, the database stored in the `pihole_data` volume takes precedence
over the compose env var — so changing the env var alone does not update a running
instance.

**On a fresh deployment:** after running `docker compose up -d`, go to Settings → DNS
and confirm `172.17.0.1#5335` appears as the custom upstream. If it shows a different
value, clear it, enter `172.17.0.1#5335`, and click Save & Apply.

### Why "Permit all origins" is checked

Pi-hole flags this as "potentially dangerous." It is safe here because UFW restricts
port 53 to `192.168.0.0/16` and `10.8.0.0/24`. No query from outside those subnets
can reach Pi-hole regardless of this setting. "Allow only local requests" would block
queries from Docker containers and WireGuard peers. "Permit all origins" is correct
when the firewall owns the boundary — it maximizes which internal clients can reach
the DNS stack without widening the external attack surface.

### No preset upstream servers checked

None of the preset upstream servers (Google, Cloudflare, Quad9, etc.) are enabled.
All upstream resolution goes through the custom entry (`172.17.0.1#5335`), which
routes to Unbound on the host. This is the whole point — no third-party resolver
ever sees the query.

________________

Uptime Kuma — Monitoring

Uptime Kuma runs in Docker on port 3001 and monitors Unbound via a DNS monitor 
querying 127.0.0.1:5335.

WHY network_mode: host — NOT A BRIDGE NETWORK

Uptime Kuma's docker-compose.yml uses network_mode: host, which removes Docker's 
network isolation and places the container directly on the host network stack. This 
is required because Ubuntu 24.04 uses nftables as its firewall backend. Legacy 
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
| CAKE SQM | Push | (script pushes) | — | Confirms CAKE qdisc is active on enp1s0; message shows live bandwidth |

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
Uptime Kuma graphs it as a time series. Threshold: 5%.

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
- Speed on home Wi-Fi through tunnel (CAKE active, Waveform test): 78.5 Mbps↓ /
  81.8 Mbps↑ — symmetric at the CAKE cap. Responsiveness: idle 14 ms, loaded
  16 ms↓ / 11 ms↑, jitter 5/5/1 ms, 0.00% packet loss
- dnsleaktest.com from phone (VPN on) shows the home WAN IP — correct, because
  the phone exits through the home connection, not a third-party VPN provider

### Does the router need a DHCP or DNS reservation for WireGuard peers?

No. The router has no role in WireGuard addressing. Peer IPs (10.8.0.x) are
assigned by the WireGuard server via `AllowedIPs` in wg0.conf — the router
never sees the 10.8.0.0/24 subnet at all. Do not create a DHCP reservation for
VPN peers.

### IP address assignments

| Peer | IP | Notes |
| ---- | -- | ----- |
| Server wg0 interface | 10.8.0.1 | Gateway; also the DNS address peers use |
| iPhone | 10.8.0.2 | |
| Mac (second peer) | 10.8.0.7 | |
| Windows laptop | 10.8.0.3 | KEY ROTATION NEEDED — private key was shared in plaintext during setup |

### Windows client security (laptop peer)

| Setting | Value | Why |
| ------- | ----- | --- |
| Network profile | Public | Blocks most unsolicited inbound connections via Windows Firewall |
| Windows Firewall | On | Confirmed enabled |

Setting the network profile to **Public** (rather than Private or Domain) is the
correct choice for a device on the home LAN that is also a VPN peer. Public profile
activates Windows Firewall's stricter inbound rules, blocking discovery and sharing
traffic from other LAN devices. The WireGuard tunnel is outbound-initiated and is
unaffected by this setting.

---

## WireGuard: adding a new peer

### Each device needs its own key pair

Never share keys between devices. Each peer's private key must be unique.
Reasons: if a device is lost, you revoke only that peer without affecting others;
WireGuard routes traffic by public key — two devices sharing one key confuse the
server about where to send return traffic; only one can realistically be connected
at a time.

### Adding a peer live (no restart)

```bash
# Add a peer without restarting wg-quick (existing tunnels stay connected)
sudo wg set wg0 peer "PEER_PUBLIC_KEY" allowed-ips 10.8.0.X/32

# Then save to wg0.conf so it survives reboot
sudo wg-quick save wg0

# Verify
sudo wg show
```

`wg-quick save wg0` writes the current live state back to `/etc/wireguard/wg0.conf`.
A manual restart is not needed — the peer is active immediately after `wg set`.

### Key derivation: the safe way to get a peer's public key

Copy/pasting base64 keys through chat, screenshots, or terminal fonts is
unreliable. The character `I` (uppercase i) and `l` (lowercase L) are
visually identical in many monospace fonts. A single wrong character produces a
valid-looking but wrong key that either fails format validation or silently
connects the wrong peer.

**Safe method — derive the public key from the private key on the server:**

```bash
PUBKEY=$(echo "PEER_PRIVATE_KEY" | wg pubkey)
echo $PUBKEY                           # verify it looks right
sudo wg set wg0 peer "$PUBKEY" allowed-ips 10.8.0.X/32
sudo wg-quick save wg0
```

The private key is processed only in the shell's memory and never written to
disk. The peer should rotate their key afterward (delete tunnel, create new
one, re-add public key) as a precaution.

**Never share your own private key in chat, screenshots, or logs.** If it
appears in plaintext anywhere, treat it as compromised and rotate immediately.
The Windows laptop peer's private key was exposed during setup — that peer
needs a new key pair.

### Do not add the server's own public key as a peer

During laptop setup, the server's public key was accidentally added as a peer:

```bash
# Wrong — this adds the server to its own peer list
sudo wg set wg0 peer "SERVER_PUBLIC_KEY" allowed-ips 10.8.0.X/32

# Remove it immediately
sudo wg set wg0 peer "SERVER_PUBLIC_KEY" remove
sudo wg-quick save wg0
```

If the server's key appears in `sudo wg show` as a peer entry, remove it.

### SSH when a full tunnel is active

With `AllowedIPs = 0.0.0.0/0`, all traffic from the VPN peer routes through
the tunnel. Attempting to SSH to the server's LAN IP (`192.168.1.118`) from
within the tunnel fails — the connection exits via the tunnel and comes back
from a `10.8.0.x` source, but the firewall only allowed SSH from
`192.168.0.0/16`.

Two fixes (both now applied):

1. **Use the WireGuard interface IP** — `ssh user@10.8.0.1` always works
   because the connection arrives on wg0 and the WG subnet is now allowed
   for SSH in `ufw/setup.sh`.

2. **UFW now allows SSH from the WG subnet** — `ufw allow in from 10.8.0.0/24
   to any port 22` is in `ufw/setup.sh`, so `ssh user@192.168.1.118` also
   works from a connected VPN peer.

### UFW: services reachable from VPN peers

When a peer runs a full tunnel, its source IP on the server is `10.8.0.x`.
Any UFW rule scoped to `192.168.0.0/16` will not match. Services that VPN
peers need must also be allowed from `10.8.0.0/24`. Currently allowed:

| Port | Service | Added in |
| ---- | ------- | -------- |
| 53/tcp+udp | Pi-hole DNS | initial WG setup |
| 22/tcp | SSH | laptop session |
| 3001/tcp | Uptime Kuma | laptop session |

Uptime Kuma (`http://192.168.1.118:3001`) was unreachable from the laptop
even after the tunnel connected because port 3001 was only open to the LAN
subnet, not the WG subnet. Adding `ufw allow from 10.8.0.0/24 to any port
3001 proto tcp` fixed it.

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

---

## CAKE / bufferbloat

**What bufferbloat is:** when a big download or upload fills the modem/router's
packet buffer, everything else has to wait behind it. A 16 ms idle ping becomes
800–1200 ms under load. This is not packet loss — all packets arrive, just late.

**Why CAKE helps:** instead of letting the buffer fill (modem has no concept of
fairness or timing), CAKE manages a smart queue in the OS. It rate-limits egress
slightly below the ISP line speed so the OS queue becomes the bottleneck. It then
applies fair queuing (each flow gets a slot) and DSCP prioritization so DNS
responses skip ahead of bulk downloads.

DNS responses are explicitly marked DSCP=CS5 by iptables mangle rules in
`cake/setup.sh` before the CAKE qdisc sees them. Without that marking, DNS
defaults to DSCP=0 (best-effort tin) and gets no priority benefit. The `wash`
option zeroes DSCP on egress so internal markings are never seen by the ISP.

### What CAKE on the t630 covers

The t630 is not inline for general LAN traffic. A laptop or phone on Wi-Fi goes
`device → Netgear R7000 → ISP`, bypassing the t630. CAKE on the t630 only
shapes traffic the t630 actually forwards:

| Traffic type | Path includes t630? | CAKE helps? |
| ------------ | ------------------- | ----------- |
| WireGuard VPN clients (upload) | Yes — exits enp1s0 | Yes |
| WireGuard VPN clients (DNS) | Yes — Pi-hole at 10.8.0.1 | Yes (diffserv4 prioritizes) |
| General LAN devices (any direction) | No — Netgear handles it | No |

**Measured impact (VPN clients):** under load, upload latency holds at 11 ms and
download at 16 ms (idle baseline 14 ms) — essentially no bufferbloat. Previous
unmanaged state was ~400–800 ms loaded. `nat` transparency lets CAKE distinguish
individual VPN clients behind the WireGuard MASQUERADE, so the iPhone and laptop
each get a fair queue slot rather than competing as a single undifferentiated flow.

### For whole-network bufferbloat: Netgear R7000

The 1200 ms download-loaded-ping spike observed in speed tests on the home
network is caused by the Netgear/modem buffer filling. The fix must be on the
device handling that bottleneck — the Netgear R7000.

The R7000 is a well-supported target for third-party firmware:

| Firmware | CAKE/fq_codel | Notes |
| -------- | ------------- | ----- |
| DD-WRT | Yes (fq_codel via QoS) | Mature, large community |
| FreshTomato | Yes (fq_codel/CAKE via QoS) | More modern UI than DD-WRT |
| OpenWrt | Yes (full CAKE) | Most capable; harder install |

FreshTomato is a reasonable starting point — it retains a familiar Tomato UI,
supports the R7000 (K26ARM build), and exposes fq_codel in QoS settings.
Steps: backup config, flash firmware via the Netgear admin UI, set QoS
download/upload caps to 90% of measured ISP speeds, enable fq_codel.

Until then, the t630 CAKE handles the VPN client case, and the home network
bufferbloat remains for direct LAN devices.

