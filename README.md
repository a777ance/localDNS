# localDNS
### A home network defined by its tunnel, not its hardware.

The WireGuard tunnel is the membrane. It defines what is inside and what is outside — not physical location, not which Wi-Fi network you are on. If you hold a key, you are inside. If you do not, you are outside.

Everything else in the stack serves that gradient:

- **Pi-hole** — filters DNS at the edge; blocks telemetry before it reaches any device
- **Unbound** — recursive DNS with DNSSEC; no third-party resolver ever sees your queries
- **Thin client (t630)** — dedicated compute for the membrane; always on, low power
- **UFW** — explicit firewall; LAN and WG subnet only, no WAN exposure
- **Uptime Kuma** — monitors every layer of the stack
- **CAKE QoS** — shapes VPN client traffic; prevents any one peer from saturating the pipe

No cloud dependencies. No bundled telemetry. No hidden behavior.

This repo is a config snapshot and rollback target. Every file maps to a specific location on the live system (see [Deploy paths](#deploy-paths)). Edits here do not take effect until manually deployed.

**The live t630 is the source of truth.** When in doubt, SSH to `192.168.1.118`.

Every commit to `main` must leave this README able to reproduce a working system on clean Ubuntu 24.04. Use feature branches for half-finished work.

---

## Hardware

- **HP t630** — AMD Carrizo GX-420GI quad-core, 16 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired only — Wi-Fi disabled)

---

## Network topology

```
ISP (Spectrum ~200/100 Mbps asymmetric)
  │
  └── Netgear R7000     192.168.1.1    main router (routing, NAT, DHCP, WAN)
        │
        └── t630        192.168.1.118  DNS + VPN server (DHCP reservation)
              │
              └── wg0   10.8.0.1/24   WireGuard tunnel interface
```

The Netgear R7000 is the sole router (routing, NAT, DHCP, WAN). The t630 hangs off the LAN as a DNS and VPN server only.

**WireGuard peers**

| Peer | Tunnel IP | Notes |
| ---- | --------- | ----- |
| t630 wg0 | 10.8.0.1 | Server gateway; DNS address peers use |
| iPhone | 10.8.0.2 | |
| Windows laptop | 10.8.0.3 | Key rotation needed — see Known issues |
| Mac | 10.8.0.7 | |

Peers 10.8.0.4 and 10.8.0.5 are present in the live wg0.conf but not documented — identify devices and add to table.

**Services**

| Service | Runtime | Port(s) | Accessible from |
| ------- | ------- | ------- | --------------- |
| Pi-hole | Docker bridge | 53 (DNS), 8080 (UI) | LAN + WG subnet |
| Unbound | host OS | 5335 | Pi-hole only (via `172.17.0.1`) |
| Uptime Kuma | Docker host-net | 3001 | LAN + WG subnet |
| WireGuard | host OS | 51820/UDP | Internet (open to Anywhere) |
| NoMachine | host OS | 4000 | LAN only |
| xrdp | host OS | 3389 | LAN only |
| SSH | host OS | 22 | LAN + WG subnet |

---

## Zero-byte drop framework

Dropping unwanted domains at DNS means no request, no payload, no parsing, no CPU cost, no battery drain.

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

**DNS execution layers**

| Component | Execution layer | Rationale |
| --------- | --------------- | --------- |
| Pi-hole | Docker container | Isolates blocklist ingestion, gravity updates, and UI |
| Unbound | Native Linux service | No bridge overhead; DNSSEC validation closest to the wire |

Pi-hole sends upstream queries to Unbound at `172.17.0.1#5335`. Inside the container `127.0.0.1` is the container's own loopback — not the host. `172.17.0.1` is the Docker bridge gateway (the host as seen from inside the container). No third-party resolver is ever in the chain.

**Uptime Kuma** runs with `network_mode: host`, which removes Docker's network isolation and places the container directly on the host network stack. This is required because Ubuntu uses nftables as its firewall backend — Docker bridge IPs are not reliably reachable from host processes on arbitrary ports. With `network_mode: host`, Uptime Kuma reaches Unbound at `127.0.0.1:5335` directly. No `ports:` mapping in the compose file; Uptime Kuma binds on the host interface directly.

---

## Repository contents

| Path | Purpose |
|------|---------|
| `wireguard/wg0.conf` | WireGuard server config — interface, peers, MASQUERADE |
| `wireguard/peer-template.conf` | Reference config for adding a new peer |
| `pihole/docker-compose.yml` | Pi-hole container |
| `uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring stack |
| `unbound/server.conf` | Unbound interfaces, ACLs, ports, security flags |
| `unbound/tuning.conf` | Cache sizes, TTL policy, threading — single source of truth |
| `unbound/remote-control.conf` | Unix socket for `unbound-control` |
| `unbound/root-auto-trust-anchor-file.conf` | DNSSEC trust anchor |
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

## Deploy paths

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
| `uptime-kuma/docker-compose.yml` | `~/uptime-kuma/docker-compose.yml` | `cd ~/uptime-kuma && docker compose up -d` |
| `ufw/setup.sh` | run directly | `sudo bash ufw/setup.sh` |
| `wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` | `sudo systemctl restart wg-quick@wg0` |
| `wireguard/peer-template.conf` | reference only | — |
| `nomachine/server.cfg` | `/usr/NX/etc/server.cfg` | `sudo /usr/NX/bin/nxserver --restart` |
| `cake/setup.sh` | `/usr/local/sbin/cake-setup.sh` | `sudo systemctl restart cake` |
| `systemd/cake.service` | `/etc/systemd/system/cake.service` | `sudo systemctl daemon-reload` |
| `systemd/gpu-performance.service` | `/etc/systemd/system/gpu-performance.service` | `sudo systemctl daemon-reload` |
| `systemd/cpu-performance.service` | `/etc/systemd/system/cpu-performance.service` | `sudo systemctl daemon-reload` |
| `systemd/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `systemd/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `systemd/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `scripts/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `scripts/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `scripts/packet-loss-monitor.sh` | `~/packet-loss-monitor.sh` (+ cron) | `crontab -e` |
| `udev/99-amdgpu-performance.rules` | `/etc/udev/rules.d/99-amdgpu-performance.rules` | `sudo udevadm control --reload-rules` |

---

## Known issues

| Issue | Action |
| ----- | ------ |
| `WEBPASSWORD` in pihole compose | Placeholder — do not commit real credentials |
| Windows laptop WireGuard key | Exposed in plaintext during setup; rotate before trusting this peer |
| WireGuard peers 10.8.0.4 and 10.8.0.5 | Present in live wg0.conf but not documented — identify devices and add to peer table |

---

## Setup

Full reproduction walkthrough for a clean Ubuntu 24.04 install.

### Part 0: Router prerequisites

**DHCP reservation:** Reserve `192.168.1.118` for the t630's MAC address in the router's LAN setup. This gives the t630 a stable address without a static IP on the OS side. If the t630 is rebuilt, the reservation keeps its address stable automatically.

**DNS for LAN clients:** Set the router's primary DNS to `192.168.1.118` and secondary to `1.1.1.1`. On the Netgear R7000 this is under Basic → Internet Setup → Domain Name Server. The router pushes these values to DHCP clients, so every device on the LAN sends queries directly to Pi-hole — Pi-hole sees individual client IPs, enabling per-device statistics.

The `1.1.1.1` secondary is a resilience choice: if the t630 goes down the network stays online, losing ad-blocking until the t630 recovers. Removing it would take the entire network offline on t630 reboots.

**Router's own DNS:** The router also uses Pi-hole for its own lookups (Advanced Home → Internet Port → Domain Name Server), so its own queries are filtered too.

**WAN security settings (Advanced → WAN Setup):**

| Setting | Value | Why |
| ------- | ----- | --- |
| NAT Filtering | Secured | Blocks unsolicited inbound packets |
| Disable SIP ALG | Yes | SIP ALG causes VoIP problems |
| Respond to ping on WAN | No | Reduces attack surface |
| Port scan / DoS protection | Enabled | Router-level rate limiting |
| DMZ | Disabled | Nothing exposed to internet directly |

---

### Part 1: Unbound

Unbound runs on the host OS, not in a container. It serves recursive DNS on port 5335 to the Pi-hole container only. `tuning.conf` is the single source of truth for all cache sizes, TTLs, and threading — do not split these into separate files.

**Install:**
```bash
sudo apt update && sudo apt install -y unbound
```

**Root hints and DNSSEC anchor:**
```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
sudo unbound-anchor -a /var/lib/unbound/root.key
sudo chown unbound:unbound /var/lib/unbound/root.key
```

**Deploy config:**
```bash
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo unbound-checkconf
sudo systemctl enable --now unbound
```

Four drop-ins loaded alphabetically from `/etc/unbound/unbound.conf.d/`:

| File | Purpose |
| ---- | ------- |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `server.conf` | Interface, port, access-control, security flags |
| `tuning.conf` | All performance and cache values |

**Verify:**
```bash
dig @127.0.0.1 -p 5335 example.com +dnssec | grep "ad;"
# 'ad' flag = DNSSEC validation working
```

**Cache persistence:**
```bash
sudo cp scripts/unbound-cache-{dump,load} /usr/local/bin/
sudo chmod +x /usr/local/bin/unbound-cache-{dump,load}
sudo mkdir -p /var/lib/unbound/cache
sudo mkdir -p /etc/systemd/system/unbound.service.d
sudo cp systemd/unbound.service.d/override.conf /etc/systemd/system/unbound.service.d/
sudo cp systemd/unbound-cache-dump.{timer,service} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unbound-cache-dump.timer
```

Cache is dumped hourly and on Unbound stop; restored 2 seconds after Unbound starts (to let the socket settle). Warm-cache performance survives reboots.

---

### Part 2: Docker CE

Install from the official Docker repository, not Ubuntu's `docker.io` package.

```bash
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group change to apply
```

---

### Part 3: Pi-hole

```bash
cd pihole/
# Set WEBPASSWORD before starting
docker compose up -d
docker compose logs -f pihole   # Ctrl-C when healthy
```

Web UI at `http://192.168.1.118:8080/admin/`.

**Set the upstream DNS in the Pi-hole UI** — this must be done manually after first deploy. The compose file sets `PIHOLE_DNS_=127.0.0.1#5335` as the initial value, which is wrong: inside the container `127.0.0.1` is the container's own loopback, not the host. The compose env var is only read on first creation of a fresh volume; after that, Pi-hole uses the value stored in its persistent database.

1. Go to Settings → DNS
2. Remove `127.0.0.1#5335` from the custom upstream field
3. Enter `172.17.0.1#5335` — the Docker bridge gateway (host as seen from container)
4. Click Save & Apply

**"Permit all origins"** — Pi-hole flags this as potentially dangerous; it is safe here because UFW restricts port 53 to `192.168.0.0/16` and `10.8.0.0/24`. No query from outside can reach Pi-hole regardless of this setting. "Permit all origins" is required to accept queries from Docker containers, bridged interfaces, and WireGuard peers (whose source IPs are `10.8.0.x`, not LAN addresses). None of the preset upstream servers (Google, Cloudflare, Quad9, etc.) should be enabled — all upstream goes through `172.17.0.1#5335`.

---

### Part 4: Uptime Kuma

```bash
mkdir -p ~/uptime-kuma
cp uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d
```

Web UI at `http://192.168.1.118:3001`. Create an admin account on first run. Data persists in `~/uptime-kuma/data/` (bind mount — back this directory up directly).

**Monitor configuration** — add these after first login:

| Friendly Name | Type | Hostname | Resolver | Port | Record |
| --- | --- | --- | --- | --- | --- |
| Unbound – Basic | DNS | `cloudflare.com` | `127.0.0.1` | `5335` | A |
| Unbound – DNSSEC | DNS | `internetsociety.org` | `127.0.0.1` | `5335` | A |
| Pi-hole – Full Chain | DNS | `cloudflare.com` | `127.0.0.1` | `53` | A |
| Pi-hole – Web UI | TCP Port | `192.168.1.118` | — | `8080` | — |
| Home Router | HTTP(s) | `http://192.168.1.1` | — | — | — |

**Resolver field gotcha:** enter the IP only — no port. Port goes in the separate Port field. `127.0.0.1:5335` in the resolver field creates an invalid double-port and causes intermittent failures.

**Diagnostic logic:** if Pi-hole Full Chain goes red but Unbound Basic stays green, the break is in the Pi-hole → Unbound link, not Unbound itself. If both go red, Unbound is the problem. Layered monitoring isolates the failure to one component.

**Packet loss monitors (Push type):**

| Friendly Name | Heartbeat Interval | Retries |
| --- | --- | --- |
| Packet Loss – Router (LAN) | 60s | 2 |
| Packet Loss – Internet (1.1.1.1) | 60s | 2 |
| CAKE SQM | 90s | 2 |

After saving each, copy the push URL (token only, strip `?status=…` from the end) into the corresponding script.

**Packet loss monitoring script:**
```bash
cp scripts/packet-loss-monitor.sh ~/packet-loss-monitor.sh
chmod +x ~/packet-loss-monitor.sh
# Edit: fill in ROUTER_PUSH_URL and INTERNET_PUSH_URL tokens, confirm ROUTER_IP
nano ~/packet-loss-monitor.sh
~/packet-loss-monitor.sh   # test manually; both Push monitors should flip green
crontab -e
```

Add to crontab:
```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

The script sends 50 pings per check (10 seconds) to fit in the 60-second window. Loss % is placed in the `ping` field so Uptime Kuma graphs it over time. `status=down` fires when loss exceeds `THRESHOLD` (default 15% — lower to 5% once router hardware is stable).

Three-hop diagnosis when loss appears:
```bash
ping -c 50 192.168.1.1   # 1. LAN/router
ping -c 50 1.1.1.1       # 2. WAN routing
ping -c 50 google.com    # 3. DNS
```
`#1 bad` = LAN issue. `#1 ok, #2 bad` = WAN/ISP. `#1 ok, #2 ok, #3 bad` = DNS. For ISP-path diagnosis: `mtr -rwzc 500 1.1.1.1`.

**CAKE monitoring script:**
```bash
cp scripts/cake-monitor.sh ~/cake-monitor.sh
chmod +x ~/cake-monitor.sh
# Edit: fill in PUSH_URL token (keep only the base URL, strip query string)
nano ~/cake-monitor.sh
~/cake-monitor.sh   # test manually
crontab -e
```

Add to crontab:
```
* * * * * /home/USERNAME/cake-monitor.sh
```

Set the CAKE SQM heartbeat interval to **90s** in Uptime Kuma, not 60s. The cron fires every 60s but scheduling jitter can push the heartbeat to second 61–62; a 90s window absorbs that without false "down" flaps. Reports `up` with the active bandwidth (e.g. `cake_active_85Mbit`) or `down` if the qdisc is missing.

**Loss threshold guidance:**

| Threshold | Meaning |
| --- | --- |
| 1–2% | Strict — catches early degradation |
| 5% | Standard — video calls start glitching |
| 10% | Lenient — things noticeably broken |
| 15% | Severe events only — router-is-overheating tier |

---

### Part 5: Firewall

```bash
sudo bash ufw/setup.sh
```

All services LAN-only (`192.168.0.0/16`): DNS 53, Unbound 5335, Pi-hole UI 8080, Uptime Kuma 3001, SSH 22, xrdp 3389, NoMachine 4000, mDNS 5353. SSH and select services are also allowed from `10.8.0.0/24` so WireGuard peers can reach them.

Port 51820/UDP (WireGuard) is open to Anywhere — the phone connects from cellular and cannot be LAN-restricted. This is the single intended exception.

The script resets and rebuilds all rules from scratch — safe to re-run.

**Services reachable from VPN peers** (source IP is `10.8.0.x` when tunneled):

| Port | Service |
| ---- | ------- |
| 53/tcp+udp | Pi-hole DNS |
| 22/tcp | SSH |
| 3001/tcp | Uptime Kuma |

---

### Part 5a: WireGuard VPN

WireGuard tunnels peers back to the home network from anywhere on cellular or untrusted Wi-Fi. DNS goes through Pi-hole, so ad-blocking and DNSSEC work identically on cellular.

**Install:**
```bash
sudo apt install -y wireguard
```

**Enable IP forwarding:**
```bash
sudo bash -c 'echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf'
sudo bash -c 'echo "net.ipv6.conf.all.forwarding=1" >> /etc/sysctl.conf'
sudo sysctl -p
```

**Generate server keys:**
```bash
wg genkey | sudo tee /etc/wireguard/server.key | wg pubkey | sudo tee /etc/wireguard/server.pub
sudo chmod 600 /etc/wireguard/server.key
```

**Deploy config:**
```bash
sudo cp wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
```

Edit `/etc/wireguard/wg0.conf`:
- Replace `REPLACE_WITH_SERVER_PRIVATE_KEY` with the contents of `/etc/wireguard/server.key`
- Replace peer `PublicKey` placeholders with each peer's actual public key

**UFW and forwarding** — `setup.sh` already sets `ufw default allow routed`. This is required. Without it, the UFW FORWARD chain drops peer traffic even when the tunnel is up and handshaking. Do not add raw `iptables -A FORWARD` rules to wg0.conf as a workaround — they land after UFW's DROP rule and are silently ignored. (See UFW forwarding failure analysis below.) PostUp/PreDown in wg0.conf manage only the MASQUERADE rule; UFW owns the FORWARD chain.

**Enable and start:**
```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show   # verify interface up, peer listed
```

**Phone client (WireGuard iOS — App Store):**

| Field | Value |
| ----- | ----- |
| Server endpoint | `<WAN-IP>:51820` |
| DNS | `10.8.0.1` |
| Allowed IPs | `0.0.0.0/0, ::/0` |
| On-Demand | Cellular + Wi-Fi enabled, no SSID exclusions |

No SSID exclusions — the tunnel stays on even at home. The home-Wi-Fi loop (phone → wg0 → enp1s0 → router → back) adds negligible latency for browsing and avoids the operational complexity of per-SSID rules.

The server public key comes from `/etc/wireguard/server.pub` on the t630. The phone's public key (generated by the app) goes into wg0.conf as the peer `PublicKey`.

**Adding additional peers (macOS or other):**

Use the **WireGuard Mac App Store app** — not Homebrew. The App Store version uses macOS's Network Extension framework. Homebrew installs `wg-quick`, a shell script that requires `sudo`, has had routing issues on modern macOS, and does not integrate with the system VPN stack.

1. Assign the next available IP (10.8.0.8, 10.8.0.9, …)
2. Add a `[Peer]` block to wg0.conf on the server: public key + `/32` AllowedIPs
3. Apply live without restart: `sudo wg set wg0 peer "PEER_PUBLIC_KEY" allowed-ips 10.8.0.X/32 && sudo wg-quick save wg0`

**Key handling — safe method:** copy/pasting base64 keys through chat or screenshots is unreliable (`I` and `l` are visually identical in many monospace fonts). Derive the public key from the private key on the server:
```bash
PUBKEY=$(echo "PEER_PRIVATE_KEY" | wg pubkey)
echo $PUBKEY
sudo wg set wg0 peer "$PUBKEY" allowed-ips 10.8.0.X/32
sudo wg-quick save wg0
```
The private key is processed only in shell memory and never written to disk. The peer should rotate their key afterward as a precaution. **Never share a private key in chat, screenshots, or logs.** If it appears in plaintext anywhere, treat it as compromised and rotate immediately. The Windows laptop peer's private key was exposed during setup and needs rotation.

**Do not add the server's own public key as a peer** — if the server's key appears in `sudo wg show` as a peer entry, remove it:
```bash
sudo wg set wg0 peer "SERVER_PUBLIC_KEY" remove
sudo wg-quick save wg0
```

**SSH from a full-tunnel peer:** with `AllowedIPs = 0.0.0.0/0`, all traffic routes through the tunnel. Use `ssh user@10.8.0.1` (the wg0 interface) rather than `ssh user@192.168.1.118` (the LAN IP), or ensure UFW allows SSH from `10.8.0.0/24` — which `ufw/setup.sh` already does.

**Verify:**
```bash
sudo wg show            # peers listed, recent handshake timestamps
ping 10.8.0.2           # phone responds when tunnel active
```

On any peer, run in order:
```
ping 10.8.0.1    # tunnel up
ping 1.1.1.1     # NAT/forwarding working
ping google.com  # DNS working
```

Each failure level points to a different problem:

| Peer config mistake | Symptom | Correct value |
| ------------------- | ------- | ------------- |
| `DNS = 172.17.0.1:5335` | DNS fails silently; "internet doesn't work" even when routing is fine. WireGuard DNS field is IP only — no port. Also, `172.17.0.1` is the Docker bridge gateway on the server and unreachable from outside. | `DNS = 10.8.0.1` |
| `Address = 10.8.0.7/24` | Client claims the entire `10.8.0.0/24` subnet on its wg0 interface; routing weirdness. | `Address = 10.8.0.7/32` |
| `AllowedIPs = 10.8.0.0/24` | Split-tunnel: web traffic bypasses VPN. "Connected" but whatismyip shows real cellular IP. | `AllowedIPs = 0.0.0.0/0, ::/0` |
| No `PersistentKeepalive` | Tunnel drops after idle when peer is behind NAT. | `PersistentKeepalive = 25` |

**Verified performance (VPN clients, CAKE active, Waveform test):** 78.5 Mbps↓ / 81.8 Mbps↑. Responsiveness: idle 14 ms, loaded 16 ms↓ / 11 ms↑, jitter 5/5/1 ms, 0.00% packet loss.

**Router has no role in WireGuard peer addressing.** The 10.8.0.0/24 subnet is entirely managed by the WireGuard server via `AllowedIPs` in wg0.conf. Do not create DHCP reservations for VPN peers.

**UFW + WireGuard forwarding — what went wrong and why:**

When a second peer (a Mac) was added, their internet stopped working after connecting. The tunnel handshaked successfully and `ping 10.8.0.1` worked, but `ping 1.1.1.1` failed.

Root cause: `wg0.conf` had PostUp lines adding raw iptables FORWARD rules:
```
iptables -A FORWARD -i wg0 -o enp1s0 -j ACCEPT
iptables -A FORWARD -i enp1s0 -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```
UFW owns the filter FORWARD chain. When `ufw default deny routed` is set, UFW inserts a DROP rule at the top of the FORWARD chain. Manually appended `-A FORWARD` rules land after UFW's DROP, so they are never reached. `sudo iptables -L FORWARD -v` confirmed: policy DROP, 0 bytes matched by the ACCEPT rules.

Fix: remove FORWARD rules from wg0.conf PostUp, and change `ufw default deny routed` to `ufw default allow routed` in `ufw/setup.sh`. UFW should own forwarding, not raw iptables added by WireGuard. MASQUERADE stays in PostUp — UFW does not manage the nat table.

---

### Part 5b: CAKE SQM (upload bufferbloat for VPN clients)

CAKE (Common Applications Kept Enhanced) eliminates bufferbloat by making the OS queue the bottleneck before the modem's unmanaged FIFO. This matters for VPN clients uploading through the tunnel — without it, upload latency spikes to 400–800 ms under load.

**Scope:** CAKE on the t630 shapes traffic on `enp1s0` egress — all traffic the t630 forwards toward the router/internet. This covers VPN client bufferbloat. It does NOT help download bufferbloat for general LAN devices (laptops, phones on Wi-Fi) — those go through the Netgear directly. For whole-network bufferbloat, the Netgear R7000 needs SQM via DD-WRT, FreshTomato, or OpenWrt. The R7000 is a well-supported target: FreshTomato (K26ARM build) supports fq_codel in QoS settings and retains a familiar UI; set QoS download/upload caps to 90% of measured ISP speeds.

| Traffic type | Path includes t630? | CAKE helps? |
| ------------ | ------------------- | ----------- |
| WireGuard VPN clients (upload) | Yes — exits enp1s0 | Yes |
| WireGuard VPN clients (DNS) | Yes — Pi-hole at 10.8.0.1 | Yes (diffserv4 prioritizes) |
| General LAN devices (any direction) | No — Netgear handles it | No |

**Install:**
```bash
sudo apt install -y iproute2

sudo cp cake/setup.sh /usr/local/sbin/cake-setup.sh
sudo chmod 755 /usr/local/sbin/cake-setup.sh
sudo cp systemd/cake.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cake
```

**Tune bandwidth cap:** open `cake/setup.sh` and adjust `UPLOAD_MBPS` to 90% of your measured ISP upload. Current value is `85` (90% of ~94 Mbps on Spectrum ~200/100). Keep the cap below the ISP ceiling so CAKE's queue fills before the modem's FIFO.

**Verify:**
```bash
systemctl status cake
tc qdisc show dev enp1s0   # should show "cake" with bandwidth and options
watch -n1 tc -s qdisc show dev enp1s0   # per-flow queue stats (live)
```

`nat` transparency lets CAKE distinguish individual VPN clients behind the WireGuard MASQUERADE, so each peer gets a fair queue slot rather than competing as a single undifferentiated flow.

---

### Part 6: GPU throttling remediation (Carrizo-specific)

The Carrizo iGPU downclocks to ~200 MHz with no display attached, making NoMachine unusable. DNS is unaffected — skip this section if you only use SSH.

**Four pieces, all required:**

**1. Kernel parameters** — edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
```
- `amdgpu.runpm=0` — disables runtime power management (cause of headless downclocking)
- `amdgpu.dpm=1` — keeps dynamic power management active
- `processor.max_cstate=1` — prevents deep CPU sleep states, improves remote desktop latency

```bash
sudo update-grub && sudo reboot
```

**2–4. Services and udev rule:**
```bash
sudo cp systemd/gpu-performance.service systemd/cpu-performance.service /etc/systemd/system/
sudo cp udev/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance cpu-performance
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```

The udev rule is the critical piece. The systemd services fire once at boot. The udev rule re-asserts `high` performance mode on every DRM subsystem event — catching display hotplug and runtime PM transitions that would otherwise re-throttle the GPU mid-session.

**Verify:**
```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # → high
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u  # → performance
```

---

### Part 7: Remote desktop

```bash
sudo apt install -y xubuntu-desktop xfce4 xfce4-goodies
sudo apt install -y cpufrequtils gamemode schedtool
```

**NoMachine** (primary, port 4000) — download `.deb` from https://www.nomachine.com/download:
```bash
sudo dpkg -i nomachine_*.deb
sudo cp nomachine/server.cfg /usr/NX/etc/server.cfg
sudo /usr/NX/bin/nxserver --restart
```

**xrdp** (RDP fallback, port 3389):
```bash
sudo apt install -y xrdp && sudo systemctl enable --now xrdp
```

**x2goserver** (low-bandwidth alternative):
```bash
sudo apt install -y x2goserver x2goserver-xsession
```

---

### Part 8: Point clients at the t630

Set the router's primary DNS to `192.168.1.118` (see Part 0). Renew DHCP leases. Verify on a client: `nslookup example.com` — server should show `192.168.1.118`.

---

## Verification

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec   # 'ad' flag = DNSSEC working
docker ps                                       # pihole + uptime-kuma both Up
sudo wg show                                    # wg0 up, peers listed
sudo ufw status verbose                         # 51820/udp Anywhere; all else LAN
tc qdisc show dev enp1s0                        # cake bandwidth 85Mbit
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # high
```

**Verification checklist:**

- [ ] `systemctl status unbound` — active
- [ ] `dig @127.0.0.1 -p 5335 example.com +dnssec` — `ad` flag present
- [ ] `docker ps` — pihole and uptime-kuma both healthy
- [ ] Pi-hole web UI at `http://192.168.1.118:8080/admin/`
- [ ] Uptime Kuma at `http://192.168.1.118:3001`
- [ ] Pi-hole Settings → DNS shows `172.17.0.1#5335` as custom upstream
- [ ] Blocked domain (`doubleclick.net`) → `0.0.0.0` from a client
- [ ] `cat /sys/class/drm/card*/device/power_dpm_force_performance_level` → `high`
- [ ] `sudo ufw status verbose` — all ports show `192.168.0.0/16` except 51820/udp which shows `Anywhere`
- [ ] `sudo wg show` — wg0 interface up, iPhone peer listed
- [ ] `tc qdisc show dev enp1s0` — shows `cake` qdisc with `bandwidth 85Mbit`
- [ ] `systemctl status unbound-cache-dump.timer` — active (waiting)
- [ ] Uptime Kuma: all DNS monitors green
- [ ] Uptime Kuma: packet loss monitors receiving heartbeats every ~60s
- [ ] Packet loss to gateway and 1.1.1.1 both below 1% under normal load

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persists hourly and restores at boot automatically
- Pi-hole named volumes backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data: back up `~/uptime-kuma/data/` directly
- Refresh root hints periodically: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`
- Check modem signal levels at `http://192.168.100.1` — downstream power should be −7 to +7 dBmV, SNR above 35 dB; out-of-spec signal levels require an ISP technician
