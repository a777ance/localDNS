# localDNS

Self-hosted DNS, VPN, and network monitoring stack on an HP t630 thin client.
Every device on the home LAN and every WireGuard peer resolves DNS through
Pi-hole (ad blocking) → Unbound (DNSSEC, Cloudflare DoT for streaming).
The WireGuard tunnel defines "inside" — not physical location.

This repo is the config snapshot, rollback target, and complete reproduction
guide. Clone it to the t630 and follow Setup below to go from fresh
Ubuntu 24.04 to a fully running stack. Edits here do not take effect until
manually deployed — **the live t630 is the source of truth.**

---

## Hardware

| | |
|---|---|
| Device | HP t630 thin client |
| CPU | AMD Carrizo GX-420GI quad-core |
| RAM | 16 GB |
| Storage | 16 GB eMMC |
| OS | Ubuntu 24.04.4 LTS, kernel 6.17 series |
| NIC | `enp1s0` (wired only — Wi-Fi disabled) |

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

**WireGuard peers**

| Peer | Tunnel IP | Notes |
| ---- | --------- | ----- |
| t630 wg0 | 10.8.0.1 | Server gateway; DNS address for all peers |
| iPhone | 10.8.0.2 | |
| Windows laptop | 10.8.0.3 | Key rotation needed — see Known issues |
| Mac | 10.8.0.7 | |

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

## How it works

### DNS resolution chain

Every query from a LAN or VPN client flows through two layers:

**Pi-hole** receives all queries, strips blocklisted domains (ad/tracker domains
answered with `0.0.0.0` — no request, no payload, no CPU cost on the client), and
forwards everything that passes to Unbound at `172.17.0.1#5335` (the Docker bridge
gateway to the host). Pi-hole does no resolver selection of its own.

**Unbound** is the single decision point for where each query goes:

- **Streaming and media domains** (Netflix, YouTube, Spotify, Steam, etc.) forward
  to Cloudflare over **DNS-over-TLS** (`1.1.1.1@853`, `forward-tls-upstream: yes`).
  The ISP sees an encrypted TLS channel instead of cleartext DNS lookups — privacy
  for speed on traffic whose destination is not sensitive.
- **Everything else** — banking, email, health, personal services, the default —
  resolves recursively with DNSSEC. Cloudflare never sees these queries. This is the
  private recursive nucleus.

The domain split lives entirely in `01-unbound/streaming-forward.conf`. **Invariant:**
never add sensitive domains to that file — doing so hands Cloudflare your private
lookups, defeating the point of the design.

If Cloudflare's port 853 is ever blocked by an ISP, `forward-first: yes` falls back
to full recursion. Streaming keeps working, just slower.

### Why Unbound runs on the host, not in Docker

DNSSEC validation needs low overhead and no bridge routing. Unbound runs directly on
the host OS at `0.0.0.0:5335`. Pi-hole reaches it via `172.17.0.1#5335` (Docker
bridge gateway). Uptime Kuma runs with `network_mode: host` so it can also reach
`127.0.0.1:5335` directly without a bridge.

### Why the host resolves its own DNS through external servers

Pi-hole publishes `0.0.0.0:53`. When Docker's proxy occupies that address, host-
originated queries to the host's own IP time out — Docker's DNAT rules don't loop
back correctly. `03-host-dns/host-dns.conf` points systemd-resolved at `9.9.9.9`
and `1.1.1.1` directly, decoupling the host's own resolution from the Docker stack.
See `network-context.md` "Host resolver" for the root-cause analysis.

### Unbound config files

Five drop-ins loaded alphabetically from `/etc/unbound/unbound.conf.d/`:

| File | Purpose |
| ---- | ------- |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `server.conf` | Interface, port, access-control, security flags |
| `streaming-forward.conf` | Domain split: streaming/media → Cloudflare DoT; all else recursive |
| `tuning.conf` | All performance and cache values — single source of truth |

`tuning.conf` is the only place to change cache sizes, TTLs, or threading. Do not
split these into separate files.

### AMD Carrizo GPU

The iGPU downclocks to ~200 MHz headless, making remote desktop unusable. Four pieces
are required to prevent it:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `gpu-performance.service` — sets `high` at boot
3. `cpu-performance.service` — locks CPU governor to `performance`
4. `99-amdgpu-performance.rules` — re-asserts `high` on every DRM event (the critical piece)

---

## Repository layout

Folders are numbered by installation order.

| Step | Path | Purpose |
|------|------|---------|
| 1 | `01-unbound/server.conf` | Interfaces, ACLs, port, security flags |
| 1 | `01-unbound/tuning.conf` | Cache sizes, TTL policy, threading — single source of truth |
| 1 | `01-unbound/streaming-forward.conf` | Domain split: streaming → Cloudflare DoT, all else → recursive |
| 1 | `01-unbound/remote-control.conf` | Unix socket for `unbound-control` |
| 1 | `01-unbound/root-auto-trust-anchor-file.conf` | DNSSEC trust anchor |
| 1 | `01-unbound/unbound-cache-dump` | Dumps Unbound cache to disk |
| 1 | `01-unbound/unbound-cache-load` | Restores cache at startup |
| 1 | `01-unbound/unbound-cache-dump.timer` | Hourly cache backup timer |
| 1 | `01-unbound/unbound-cache-dump.service` | One-shot cache backup worker |
| 1 | `01-unbound/unbound.service.d/override.conf` | Hooks cache load/dump into service lifecycle |
| 2 | *(Docker CE — install only, no config files)* | |
| 3 | `02-pihole/docker-compose.yml` | Pi-hole container |
| 4 | `03-host-dns/host-dns.conf` | Host resolver fix — external DNS after Pi-hole takes port 53 |
| 5 | `04-ufw/setup.sh` | Firewall: LAN + WG subnet, WireGuard WAN port open to Anywhere |
| 6 | `05-wireguard/wg0.conf` | WireGuard server config — interface, peers, NAT |
| 6 | `05-wireguard/peer-template.conf` | Annotated reference config for adding a new peer |
| 7 | `06-cake/setup.sh` | CAKE QoS script — apply qdisc and DNS DSCP marking |
| 7 | `06-cake/cake.service` | CAKE systemd service |
| 8 | `07-uptime-kuma/docker-compose.yml` | Uptime Kuma monitoring container |
| 8 | `07-uptime-kuma/packet-loss-monitor.sh` | Packet loss cron monitor feeding Uptime Kuma Push |
| 8 | `07-uptime-kuma/cake-monitor.sh` | CAKE qdisc health monitor feeding Uptime Kuma Push |
| 9 | `08-gpu-performance/gpu-performance.service` | AMD GPU forced to high-performance at boot |
| 9 | `08-gpu-performance/cpu-performance.service` | CPU governor locked to performance |
| 9 | `08-gpu-performance/99-amdgpu-performance.rules` | Re-asserts GPU profile on every DRM event |
| 10 | `09-remote-desktop/server.cfg` | NoMachine server config |

---

## Setup

### Before you begin

**Clone the repo to the t630.** All commands below use paths relative to the repo
root. Without this, every `cp` command fails immediately.

```bash
git clone https://github.com/a777ance/localdns ~/localdns
cd ~/localdns
```

---

### Step 0: Router — DHCP reservation

Do this **before** touching the t630 so it boots with a stable address from the start.

Find the t630's MAC address:
```bash
ip link show enp1s0   # MAC is the link/ether value
```

On the Netgear R7000: Advanced → Setup → LAN Setup → Address Reservation. Reserve
`192.168.1.118` for the t630's MAC.

Do **not** set the router's DNS to `192.168.1.118` yet. That happens in Step 11,
after the full stack is verified. Setting it now breaks name resolution for every
LAN device before Pi-hole is ready.

---

### Step 1: Unbound — Recursive DNS

Unbound runs on the host OS, not in a container. It is the DNS decision point — all
queries that pass Pi-hole's blocklist come here. It must exist before Pi-hole.

#### Install

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y unbound ca-certificates
```

#### Root hints and DNSSEC anchor

```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
sudo unbound-anchor -a /var/lib/unbound/root.key
sudo chown unbound:unbound /var/lib/unbound/root.key
```

#### Deploy configuration

```bash
sudo cp 01-unbound/*.conf /etc/unbound/unbound.conf.d/
sudo unbound-checkconf
sudo systemctl enable --now unbound
```

Five drop-ins deploy together. `unbound-checkconf` must pass before the next command.

#### Verify

```bash
dig @127.0.0.1 -p 5335 example.com +dnssec | grep "ad;"
# 'ad' flag = DNSSEC validation working

sudo unbound-control lookup netflix.com   # → forwarding request to 1.1.1.1@853 / 1.0.0.1@853
sudo unbound-control lookup chase.com    # → iterative delegation (recursive, private)
```

#### Step 1a: Encrypted streaming forward-path (Cloudflare DoT)

Already deployed by the `cp` above. `streaming-forward.conf` forwards streaming and
media domains to Cloudflare over DNS-over-TLS at port 853. Everything not listed
resolves recursively — Cloudflare never sees those queries.

Confirm end-to-end:
```bash
dig @127.0.0.1 -p 5335 netflix.com +short    # resolves → DoT path works
sudo unbound-control lookup chase.com        # iterative delegation → private recursive path
```

**Invariant:** never add sensitive domains (banking, email, health) to
`streaming-forward.conf` — that hands Cloudflare your private lookups.

#### Step 1b: Cache persistence

Cache dumps hourly and on Unbound stop; restores 2 seconds after start (socket settle
time). Warm cache survives reboots.

```bash
sudo cp 01-unbound/unbound-cache-dump 01-unbound/unbound-cache-load /usr/local/bin/
sudo chmod +x /usr/local/bin/unbound-cache-dump /usr/local/bin/unbound-cache-load
sudo mkdir -p /var/lib/unbound/cache
sudo mkdir -p /etc/systemd/system/unbound.service.d
sudo cp 01-unbound/unbound.service.d/override.conf /etc/systemd/system/unbound.service.d/
sudo cp 01-unbound/unbound-cache-dump.timer \
        01-unbound/unbound-cache-dump.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unbound-cache-dump.timer
```

---

### Step 2: Docker CE

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
```

**Log out and back in** (or `exec su -l $USER` in the same shell) before the next
step — the `docker` group change is not active in the current session. Running
`docker compose` without this produces a "permission denied on socket" error.

---

### Steps 3 + 4: Pi-hole and Host DNS Fix

**These two steps must run back-to-back without pausing between them.**

The moment Pi-hole starts and binds port 53, Docker's proxy occupies `0.0.0.0:53` —
including `127.0.0.53`, which is systemd-resolved's stub address. Host DNS breaks
immediately. Any command requiring DNS (including `docker compose logs`, `apt`,
`curl`) will fail with "Temporary failure in name resolution" until Step 4 completes.
Do not run any other commands between starting Pi-hole and deploying the host DNS fix.

#### Step 3: Start Pi-hole

```bash
# 1. Set a real password before starting — the default is a placeholder
nano 02-pihole/docker-compose.yml
# Change: WEBPASSWORD: "CHANGE_ME"
# To:     WEBPASSWORD: "your-actual-password"

# 2. Copy compose file to its operational location and start
mkdir -p ~/pihole
cp 02-pihole/docker-compose.yml ~/pihole/
cd ~/pihole && docker compose up -d
```

#### Step 4: Fix host DNS immediately

```bash
cd ~/localdns
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo cp 03-host-dns/host-dns.conf /etc/systemd/resolved.conf.d/
sudo systemctl restart systemd-resolved
getent hosts security.ubuntu.com   # must return an IP — host DNS is working
```

Now it is safe to check Pi-hole:
```bash
docker compose -f ~/pihole/docker-compose.yml logs -f pihole   # Ctrl-C when healthy
```

Web UI at `http://192.168.1.118:8080/admin/`.

#### Confirm Pi-hole upstream DNS in the UI

Go to Settings → DNS. Verify:
1. Custom upstream shows exactly: `172.17.0.1#5335`
2. No preset resolvers (Google, Cloudflare, Quad9) are checked

The `PIHOLE_DNS_: "172.17.0.1#5335"` env var seeds this on a fresh volume, but
confirm it in the UI after first start. Do not add public resolvers — Pi-hole
forwards everything to Unbound, and Unbound owns the streaming/personal split.
Adding public resolvers here would race them for every query, including sensitive ones.

#### Set Pi-hole interface mode

Settings → DNS → Interface: set to **"Permit all origins"**. This is required for
Pi-hole to accept queries from WireGuard tunnel clients (`10.8.0.x`) and Docker
containers. Safe here because UFW (next step) restricts access at the network layer.

> **UFW and Docker port 53:** Docker inserts DNAT rules into the `DOCKER` iptables
> chain, which processes before UFW's INPUT chain. Pi-hole's published port 53 is not
> restricted by UFW's `from 192.168.0.0/16` rule — Docker handles that routing
> directly. The router's NAT is the outer boundary for WAN access. Unbound's port 5335
> is a host-resident service and is correctly protected by UFW via the
> `allow in on docker0` rule.

---

### Step 5: UFW Firewall

Lock down before opening the WAN port in Step 6.

```bash
sudo bash 04-ufw/setup.sh
sudo ufw status verbose   # verify: 51820/udp Anywhere; all else LAN-only
```

Rules applied:

| Port | Protocol | Allowed from |
|------|----------|--------------|
| 53 | TCP/UDP | `192.168.0.0/16` + `10.8.0.0/24` |
| 5335 | TCP/UDP | `192.168.0.0/16` + docker0 bridge |
| 22 | TCP | `192.168.0.0/16` + `10.8.0.0/24` |
| 8080 | TCP | `192.168.0.0/16` |
| 3001 | TCP | `192.168.0.0/16` + `10.8.0.0/24` |
| 3389 | TCP | `192.168.0.0/16` |
| 4000 | TCP/UDP | `192.168.0.0/16` |
| 5353 | UDP | `192.168.0.0/16` |
| **51820** | **UDP** | **Anywhere** (WireGuard — phone connects from cellular) |

`ufw default allow routed` is set by the script. This is required for WireGuard to
forward peer traffic out `enp1s0`. Do not add raw `iptables -A FORWARD` rules as a
workaround — they land after UFW's DROP rule and are silently ignored.

---

### Step 6: WireGuard VPN

WireGuard tunnels peers back to the home network from anywhere on cellular or
untrusted Wi-Fi. DNS routes through Pi-hole over the tunnel, so ad-blocking and
DNSSEC work identically on cellular.

UFW's `allow routed` (Step 5) must be in place before enabling WireGuard — without
it the FORWARD chain drops peer traffic silently.

#### Install

```bash
sudo apt install -y wireguard
```

#### Enable IP forwarding

This uses a `sysctl.d` drop-in (idempotent — safe to re-run):

```bash
printf 'net.ipv4.ip_forward=1\nnet.ipv6.conf.all.forwarding=1\n' \
  | sudo tee /etc/sysctl.d/99-wireguard-forward.conf
sudo sysctl --system
```

#### Generate server keys

```bash
wg genkey | sudo tee /etc/wireguard/server.key | wg pubkey | sudo tee /etc/wireguard/server.pub
sudo chmod 600 /etc/wireguard/server.key
```

#### Deploy config

```bash
sudo cp 05-wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
```

Edit `/etc/wireguard/wg0.conf` — three required edits before starting WireGuard:

1. Replace `REPLACE_WITH_SERVER_PRIVATE_KEY` with: `sudo cat /etc/wireguard/server.key`
2. Replace `REPLACE_WITH_PHONE_PUBLIC_KEY` with the phone's WireGuard public key
3. **Review the Mac and laptop peer blocks.** Any `[Peer]` block without a valid
   Curve25519 public key (real base64, not a placeholder) will cause `wg-quick` to
   fail at parse time with an invalid-key error. Comment out any peer block you do not
   have a real key for yet — you can add peers later with
   `sudo systemctl reload wg-quick@wg0` (no restart needed).

#### Enable and start

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show   # verify: interface up, peer listed
```

#### Phone client (WireGuard iOS/Android — App Store)

| Field | Value |
| ----- | ----- |
| Server endpoint | `<WAN-IP>:51820` |
| DNS | `10.8.0.1` |
| Allowed IPs | `0.0.0.0/0` (IPv4 only — do **not** add `::/0`, see Known issues) |
| PersistentKeepalive | 25 |
| On-Demand | Cellular + Wi-Fi enabled, no SSID exclusions |

Server public key: `sudo cat /etc/wireguard/server.pub`

#### Adding peers (Mac, additional devices)

See `05-wireguard/peer-template.conf` — fully annotated, with common mistakes called
out. Assign the next free tunnel IP starting at `10.8.0.8` (`10.8.0.2`–`10.8.0.7`
are already in use). Add a `[Peer]` block to `wg0.conf` and reload:

```bash
sudo systemctl reload wg-quick@wg0   # no restart; peers can be added live
```

Safe key derivation method (avoids base64 transcription errors):
```bash
# On the server — give the peer's private key temporarily; derive pubkey here
PUBKEY=$(echo "PEER_PRIVATE_KEY_HERE" | wg pubkey)
sudo wg set wg0 peer "$PUBKEY" allowed-ips 10.8.0.X/32
sudo wg-quick save wg0
# Peer should immediately rotate their key after confirming the tunnel works
```

#### Verify

```bash
sudo wg show              # peers listed, recent handshake timestamps
ping 10.8.0.2             # phone responds when tunnel is active
```

From the peer, test in order — each failure level points to a different problem:
```
ping 10.8.0.1    # tunnel up
ping 1.1.1.1     # NAT/forwarding working
ping google.com  # DNS working
```

---

### Step 7: CAKE SQM

CAKE eliminates upload bufferbloat. Without it, latency spikes 400–800 ms under VPN
upload load. With it: 11 ms loaded vs 14 ms idle (measured on Spectrum ~200/100 Mbps).

**Scope:** shapes `enp1s0` egress — all traffic the t630 forwards toward the router.
Covers upload bufferbloat for WireGuard VPN clients. Does not address download
bufferbloat for general LAN devices (the Netgear R7000 is the correct fix point
for that; DD-WRT/FreshTomato both support CAKE).

#### Install

```bash
# iproute2 (tc) is already present on Ubuntu 24.04
sudo cp 06-cake/setup.sh /usr/local/sbin/cake-setup.sh
sudo chmod 755 /usr/local/sbin/cake-setup.sh
sudo cp 06-cake/cake.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cake
```

#### Tune bandwidth cap

Open `06-cake/setup.sh` and adjust `UPLOAD_MBPS` to 90% of your measured ISP upload
**before** deploying. Current value: `85` (90% of ~94 Mbps on Spectrum). Keep it
below the ISP ceiling so CAKE's queue fills before the modem's unmanaged FIFO.

#### DNS priority marking

`cake-setup.sh` marks DNS response packets (source port 53, UDP and TCP) with DSCP
EF. CAKE's `diffserv4` scheduler places them in the highest-priority tin — DNS answers
skip bulk traffic so every new connection resolves before its first byte is queued.

#### Verify

```bash
systemctl status cake
tc qdisc show dev enp1s0                                       # → cake bandwidth 85Mbit
sudo iptables -t mangle -L POSTROUTING -v | grep DSCP         # → two rules, sport 53 → EF
watch -n1 tc -s qdisc show dev enp1s0                         # live queue stats
```

---

### Step 8: Uptime Kuma

Set up after everything else exists to monitor — the CAKE script depends on CAKE
being installed first.

```bash
mkdir -p ~/uptime-kuma
cp 07-uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d
```

Web UI at `http://192.168.1.118:3001`. Create an admin account on first run.
Data persists in `~/uptime-kuma/data/` (bind mount — back this directory up directly).

Uptime Kuma uses `network_mode: host`, placing it on the host network stack. This lets
it reach Unbound at `127.0.0.1:5335` directly — unlike Pi-hole (Docker bridge), which
must use `172.17.0.1#5335`.

#### DNS monitors

Create these in the Uptime Kuma UI (Add Monitor):

| Friendly name | Type | Hostname | Resolver | Port | Record |
| --- | --- | --- | --- | --- | --- |
| Unbound – Basic | DNS | `cloudflare.com` | `127.0.0.1` | `5335` | A |
| Unbound – DNSSEC | DNS | `internetsociety.org` | `127.0.0.1` | `5335` | A |
| Pi-hole – Full Chain | DNS | `cloudflare.com` | `127.0.0.1` | `53` | A |
| Pi-hole – Web UI | TCP Port | `192.168.1.118` | — | `8080` | — |
| Home Router | HTTP(s) | `http://192.168.1.1` | — | — | — |

Enter IP only in the resolver field — port goes in the separate Port field.
`127.0.0.1:5335` in the resolver field creates an invalid double-port and causes
intermittent failures.

#### Packet loss monitors (Push type)

Create three Push monitors in the UI:

| Friendly name | Heartbeat interval | Retries |
| --- | --- | --- |
| Packet Loss – Router (LAN) | 60s | 2 |
| Packet Loss – Internet (1.1.1.1) | 60s | 2 |
| CAKE SQM | 90s | 2 |

After saving each, copy the push URL token (strip `?status=…` — keep only the base
URL up to and including the token) into the corresponding script.

#### Packet loss monitoring script

```bash
cp 07-uptime-kuma/packet-loss-monitor.sh ~/
chmod +x ~/packet-loss-monitor.sh
# Fill in ROUTER_PUSH_URL and INTERNET_PUSH_URL with your tokens
nano ~/packet-loss-monitor.sh

# Test manually before scheduling — both monitors must flip green within 60s
~/packet-loss-monitor.sh

# Once confirmed working, add to crontab (replace USER with your actual username)
crontab -e
```

Add to crontab:
```
* * * * * /home/USER/packet-loss-monitor.sh
```

The script sends 50 pings at 0.2 s intervals (~10 s total) so it fits in the 60-second
window. Loss percentage is placed in the `ping` field so Uptime Kuma graphs it over time.

#### CAKE monitoring script

```bash
cp 07-uptime-kuma/cake-monitor.sh ~/
chmod +x ~/cake-monitor.sh
# Fill in PUSH_URL with your token
nano ~/cake-monitor.sh

# Test manually — CAKE monitor must flip green
~/cake-monitor.sh

crontab -e
```

Add to crontab:
```
* * * * * /home/USER/cake-monitor.sh
```

CAKE SQM heartbeat is 90s (not 60s) — cron fires every 60s but scheduling jitter
can push the heartbeat to second 61–62; the 90s window absorbs that without false
"down" flaps.

**Packet loss threshold guidance:**

| Threshold | Meaning |
| --- | --- |
| 1–2% | Strict — catches early degradation |
| 5% | Standard — video calls start glitching |
| 10% | Lenient — things noticeably broken |
| 15% | Severe events only |

---

### Step 9: GPU Performance

**Only required for remote desktop.** DNS and VPN are unaffected by the GPU clock
speed — skip this step entirely if you only use SSH.

**Requires a reboot.** Do this before installing NoMachine.

#### 1. Kernel parameters

Edit `/etc/default/grub`. Find the `GRUB_CMDLINE_LINUX_DEFAULT` line and **append**
the flags to whatever is already there — do not replace the existing value.

If the current line is:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
```

Change it to:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
```

- `amdgpu.runpm=0` — disables runtime power management (root cause of headless downclocking)
- `amdgpu.dpm=1` — keeps dynamic power management active
- `processor.max_cstate=1` — prevents deep CPU sleep; improves remote desktop latency

```bash
sudo update-grub && sudo reboot
```

#### 2–4. Services and udev rule

After rebooting and SSH-ing back in:

```bash
cd ~/localdns
sudo cp 08-gpu-performance/gpu-performance.service \
        08-gpu-performance/cpu-performance.service /etc/systemd/system/
sudo cp 08-gpu-performance/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance cpu-performance
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```

The udev rule is the critical piece. The systemd services fire once at boot. The udev
rule re-asserts `high` on every DRM event — catching display hotplug and runtime PM
transitions that would otherwise re-throttle the GPU mid-session.

#### Verify

```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level   # → high
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u  # → performance
```

---

### Step 10: Remote Desktop

```bash
sudo apt install -y xubuntu-desktop xfce4 xfce4-goodies
sudo apt install -y cpufrequtils gamemode schedtool
```

**NoMachine** (primary, port 4000) — download the `.deb` from nomachine.com
(Linux → DEB package for x86_64):

```bash
# After downloading to the current directory:
sudo dpkg -i nomachine_*.deb
sudo cp 09-remote-desktop/server.cfg /usr/NX/etc/server.cfg
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

### Step 11: Point LAN Clients at t630

Do this **last**, after every item on the verification checklist below passes.

On the Netgear R7000: Basic → Internet Setup → Domain Name Server (DNS Address):
- Primary DNS: `192.168.1.118`
- Secondary DNS: `1.1.1.1` (resilience — if the t630 goes down the network stays
  online, losing ad-blocking until it recovers)

Renew DHCP leases on all client devices. Verify on any client:
```
nslookup example.com   # Server field must show 192.168.1.118
```

---

## Verification checklist

Run these after completing all steps to confirm the full stack is operating. Every
item must pass before Step 11.

- [ ] `systemctl status unbound` — active
- [ ] `dig @127.0.0.1 -p 5335 example.com +dnssec` — `ad` flag present (DNSSEC working)
- [ ] `dig @127.0.0.1 -p 5335 netflix.com +short` — resolves (Cloudflare DoT end-to-end)
- [ ] `sudo unbound-control lookup netflix.com` → `forwarding request` to `1.1.1.1@853` / `1.0.0.1@853`
- [ ] `sudo unbound-control lookup chase.com` → iterative delegation (private, never forwarded)
- [ ] `docker ps` — pihole and uptime-kuma both Up and healthy
- [ ] Pi-hole web UI at `http://192.168.1.118:8080/admin/`
- [ ] Pi-hole Settings → DNS → custom upstream: exactly `172.17.0.1#5335`, no preset resolvers checked
- [ ] Pi-hole Settings → DNS → Interface: "Permit all origins"
- [ ] `getent hosts security.ubuntu.com` — returns IP (host resolver independent of Pi-hole)
- [ ] `sudo ufw status verbose` — all ports show `192.168.0.0/16` except 51820/udp → `Anywhere`
- [ ] `sudo wg show` — wg0 interface up, iPhone peer listed with recent handshake
- [ ] `systemctl status cake` — active
- [ ] `tc qdisc show dev enp1s0` — shows `cake` qdisc with `bandwidth 85Mbit`
- [ ] `sudo iptables -t mangle -L POSTROUTING -v | grep DSCP` — two rules marking sport 53 as EF
- [ ] `systemctl status unbound-cache-dump.timer` — active (waiting)
- [ ] Uptime Kuma at `http://192.168.1.118:3001` — all DNS monitors green
- [ ] Uptime Kuma: packet loss monitors receiving heartbeats (`crontab -l` confirms jobs)
- [ ] Packet loss to gateway and 1.1.1.1 both below threshold under normal load
- [ ] Blocked domain (`doubleclick.net`) → `0.0.0.0` from a LAN client
- [ ] `cat /sys/class/drm/card*/device/power_dpm_force_performance_level` → `high`
- [ ] `nslookup example.com` from LAN client → Server shows `192.168.1.118`

---

## Configuration reference

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `01-unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `01-unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `01-unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `01-unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `01-unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` | `sudo systemctl restart unbound` |
| `01-unbound/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `01-unbound/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `01-unbound/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `01-unbound/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `01-unbound/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `02-pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
| `03-host-dns/host-dns.conf` | `/etc/systemd/resolved.conf.d/host-dns.conf` | `sudo systemctl restart systemd-resolved` |
| `04-ufw/setup.sh` | run directly | `sudo bash 04-ufw/setup.sh` |
| `05-wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` | `sudo systemctl restart wg-quick@wg0` |
| `05-wireguard/peer-template.conf` | reference only | — |
| `06-cake/setup.sh` | `/usr/local/sbin/cake-setup.sh` | `sudo systemctl restart cake` |
| `06-cake/cake.service` | `/etc/systemd/system/cake.service` | `sudo systemctl daemon-reload` |
| `07-uptime-kuma/docker-compose.yml` | `~/uptime-kuma/docker-compose.yml` | `cd ~/uptime-kuma && docker compose up -d` |
| `07-uptime-kuma/packet-loss-monitor.sh` | `~/packet-loss-monitor.sh` (+ cron) | `crontab -e` |
| `07-uptime-kuma/cake-monitor.sh` | `~/cake-monitor.sh` (+ cron) | `crontab -e` |
| `08-gpu-performance/gpu-performance.service` | `/etc/systemd/system/gpu-performance.service` | `sudo systemctl daemon-reload` |
| `08-gpu-performance/cpu-performance.service` | `/etc/systemd/system/cpu-performance.service` | `sudo systemctl daemon-reload` |
| `08-gpu-performance/99-amdgpu-performance.rules` | `/etc/udev/rules.d/99-amdgpu-performance.rules` | `sudo udevadm control --reload-rules` |
| `09-remote-desktop/server.cfg` | `/usr/NX/etc/server.cfg` | `sudo /usr/NX/bin/nxserver --restart` |

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persists hourly and restores at boot automatically
- Pi-hole data backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data: back up `~/uptime-kuma/data/` directly
- Refresh root hints: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`
- Reset firewall rules: `sudo bash 04-ufw/setup.sh` (idempotent — safe to re-run)
- Add a streaming domain to Cloudflare DoT: append a `forward-zone:` block to `01-unbound/streaming-forward.conf`, deploy to `/etc/unbound/unbound.conf.d/`, and `sudo systemctl restart unbound`. Never add sensitive domains.
- Add a WireGuard peer: see `05-wireguard/peer-template.conf`. Next free IP starts at `10.8.0.8`. Use `sudo systemctl reload wg-quick@wg0` — no restart needed.

---

## Known issues

| Issue | Status | Action |
| ----- | ------ | ------ |
| `WEBPASSWORD` in pihole compose | Open | Placeholder — must be changed before first `docker compose up` |
| Windows laptop WireGuard key | Open | Private key was exposed during setup; rotate before trusting this peer |
| WireGuard peers 10.8.0.4–10.8.0.6 | Open | Present in live `wg0.conf` but not documented — identify devices and add to peer table |
| WireGuard `::/0` IPv6 black hole | Documented | Server is IPv4-only in-tunnel; do not add `::/0` to peer AllowedIPs. IPv6 traffic black-holes silently: handshake succeeds, pages hang. Use `0.0.0.0/0` only. Leak-free dual-stack fix (ULA + NAT66) in `network-context.md`. |
| VPN peer DNS over the tunnel | Unresolved | Phone (`10.8.0.2`) intermittently can't resolve via Pi-hole at `10.8.0.1`: queries reach `wg0` (tcpdump confirms) but replies don't return. First fix: confirm Pi-hole → Settings → DNS → Interface is "Permit all origins". If still broken, run Pi-hole with `network_mode: host` like Uptime Kuma. Stopgap: set peer DNS to `1.1.1.1`. |
| Live Pi-hole upstreams ≠ repo | Check on deploy | Dashboard may show legacy resolvers (`8.8.8.8`, Quad9, etc.) retained in the `pihole_data` Docker volume from a prior install. On every fresh deploy, confirm Pi-hole UI → Settings → DNS shows only `172.17.0.1#5335`. |

---

## Further reading

- **INSTALL-NOTES.md** — fresh install simulation: every known break point, its
  severity, and what was fixed
- **network-context.md** — design rationale: Docker networking, UFW/WireGuard
  forwarding, CAKE bufferbloat scope, Uptime Kuma monitor stack, WireGuard IPv6
- **CLAUDE.md** — structural summary and deploy-path reference for AI assistants
  working on this repo
