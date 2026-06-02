# Setup Guide

Full reproduction walkthrough for the localDNS stack on the HP t630 thin client.
Start from a **fresh Ubuntu 24.04 LTS install** — nothing else assumed.

## Hardware and OS

- HP t630 (AMD Carrizo GX-420GI quad-core, 16 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Ethernet (enp1s0), Wi-Fi disabled

---

## Step 0: Router — DHCP Reservation

Do this **before** touching the t630 so it boots with a stable address from the start.

**DHCP reservation:** Reserve `192.168.1.118` for the t630's MAC address in the
router's LAN setup (Netgear R7000: Advanced → Setup → LAN Setup → Address
Reservation). This gives the t630 a fixed IP without a static OS-level config.

> **Note:** Do NOT set the router's DNS to `192.168.1.118` yet. That happens last
> (Step 11), after the full stack is running and verified. Setting it now will break
> name resolution for every LAN device before Pi-hole is ready.

See `network-context.md` for full router setting rationale.

---

## Step 1: Unbound — Recursive DNS (`01-unbound/`)

Unbound runs on the host OS, not in a container. It is the DNS decision point:
personal/sensitive queries resolve recursively with DNSSEC (no third party ever sees
them); high-volume streaming domains forward to Cloudflare over DNS-over-TLS for speed.
It must exist **before** Pi-hole, because Pi-hole forwards everything to it.

### Install

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y unbound ca-certificates
```

### Root hints and DNSSEC anchor

```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
sudo unbound-anchor -a /var/lib/unbound/root.key
sudo chown unbound:unbound /var/lib/unbound/root.key
```

### Deploy configuration

```bash
sudo cp 01-unbound/*.conf /etc/unbound/unbound.conf.d/
sudo unbound-checkconf
sudo systemctl enable --now unbound
```

Five drop-ins deploy together: `server.conf` (network/security), `tuning.conf`
(cache, TTLs, threading — single source of truth), `streaming-forward.conf` (domain
split — see Step 1a), `remote-control.conf` (Unix socket), `root-auto-trust-anchor-file.conf`
(DNSSEC trust anchor).

### Verify

```bash
dig @127.0.0.1 -p 5335 example.com +dnssec | grep "ad;"
# 'ad' flag = DNSSEC validation working

sudo unbound-control lookup netflix.com   # → "forwarding request" to 1.1.1.1@853 / 1.0.0.1@853
sudo unbound-control lookup chase.com     # → iterative delegation (recursive, private)
```

### Step 1a: Encrypted streaming forward-path (Cloudflare DoT)

`streaming-forward.conf` forwards high-volume, low-sensitivity domains (Netflix,
YouTube, Spotify, Steam, etc.) to Cloudflare over **DNS-over-TLS** at port 853.
The ISP sees an encrypted channel instead of cleartext lookups. Personal, banking,
and sensitive domains always resolve recursively — Cloudflare never sees those queries.

**There is no separate daemon.** Unbound does DoT natively. The `tls-cert-bundle`
directive in `streaming-forward.conf` points at `/etc/ssl/certs/ca-certificates.crt`
(provided by `ca-certificates`, installed above). If port 853 is ever blocked by an
ISP, `forward-first: yes` falls back to recursion — streaming keeps working.

This is already deployed by the `sudo cp` above. Confirm it works:

```bash
sudo unbound-control lookup netflix.com     # → forwarding request to 1.1.1.1@853
dig @127.0.0.1 -p 5335 netflix.com +short   # → resolves (DoT path works end-to-end)
sudo unbound-control lookup chase.com       # → iterative delegation (private, never forwarded)
```

**Invariant:** never add sensitive domains (banking, email, health) to `streaming-forward.conf`.
That would hand Cloudflare your private lookups.

### Step 1b: Cache persistence

Cache is dumped hourly and on Unbound stop; restored 2 s after start (socket settle
time). Warm-cache performance survives reboots.

```bash
sudo cp 01-unbound/unbound-cache-dump 01-unbound/unbound-cache-load /usr/local/bin/
sudo chmod +x /usr/local/bin/unbound-cache-dump /usr/local/bin/unbound-cache-load
sudo mkdir -p /var/lib/unbound/cache
sudo mkdir -p /etc/systemd/system/unbound.service.d
sudo cp 01-unbound/unbound.service.d/override.conf /etc/systemd/system/unbound.service.d/
sudo cp 01-unbound/unbound-cache-dump.timer 01-unbound/unbound-cache-dump.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unbound-cache-dump.timer
```

---

## Step 2: Docker CE

Install from the official Docker repository, not Ubuntu's `docker.io` package.
No repo files — install only.

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
# Log out and back in for the group change to apply before proceeding
```

---

## Step 3: Pi-hole (`02-pihole/`)

Pi-hole filters DNS at the edge. It sits in front of Unbound — every client on the
LAN and VPN sends queries here first. Pi-hole strips ad/tracker domains, then forwards
everything else to Unbound at `172.17.0.1#5335` (the Docker bridge gateway to the
host; `127.0.0.1` would be the container's own loopback and would not reach Unbound).

```bash
cd 02-pihole/
# Edit docker-compose.yml: set WEBPASSWORD before starting
docker compose up -d
docker compose logs -f pihole   # Ctrl-C when healthy
```

Web UI at `http://192.168.1.118:8080/admin/`.

### Confirm the upstream DNS in Pi-hole UI

The compose env var `PIHOLE_DNS_=172.17.0.1#5335` seeds this on a fresh volume.
After the container starts, verify in Settings → DNS:

1. Custom upstream shows exactly: `172.17.0.1#5335`
2. No preset resolvers (Google, Cloudflare, Quad9) are checked

**Do not add public resolvers here.** Pi-hole forwards everything to Unbound, and
Unbound owns the streaming/personal split. Adding public resolvers would race them
for every query — including sensitive personal ones — and defeat the private path.

### Interface setting

Set Settings → DNS → Interface to **"Permit all origins"** — safe here because UFW
(Step 4) restricts port 53 to `192.168.0.0/16`. This setting is required so Pi-hole
accepts queries from Docker containers and bridged interfaces.

---

## Step 4: Host DNS Fix (`03-host-dns/`)

**Do this immediately after Pi-hole starts.** Once Pi-hole binds `0.0.0.0:53`, the
t630 can no longer resolve its own queries through it — host-originated DNS requests
time out. Without this fix, `apt`, `git`, `curl`, and every other host tool breaks.

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo cp 03-host-dns/host-dns.conf /etc/systemd/resolved.conf.d/
sudo systemctl restart systemd-resolved
getent hosts security.ubuntu.com   # must return an IP — host resolution works
```

This points the host at external resolvers (`1.1.1.1`, `9.9.9.9`) independently of
the Docker stack. See `network-context.md` "Host resolver" for the root-cause analysis.

If `/etc/resolv.conf` still shows `nameserver 127.0.0.1`, that entry is pinned in
`/etc/netplan/*.yaml`. It is harmless (external resolvers are tried first) but can
be removed there for tidiness.

---

## Step 5: UFW Firewall (`04-ufw/`)

Lock down the machine **before** opening a WAN port in the next step.

```bash
sudo bash 04-ufw/setup.sh
```

What this sets:

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

The script also sets `ufw default allow routed` — required for WireGuard to forward
peer traffic out `enp1s0`. Do not add raw `iptables -A FORWARD` rules as a workaround;
they land after UFW's DROP rule and are silently ignored.

```bash
sudo ufw status verbose   # verify: 51820/udp Anywhere; all else LAN-only
```

---

## Step 6: WireGuard VPN (`05-wireguard/`)

WireGuard tunnels peers back to the home network from anywhere on cellular or
untrusted Wi-Fi. DNS routes through Pi-hole over the tunnel, so ad-blocking and
DNSSEC work identically on cellular.

UFW's `allow routed` (Step 5) must already be in place before enabling WireGuard —
without it, the FORWARD chain drops peer traffic silently.

### Install

```bash
sudo apt install -y wireguard
```

### Enable IP forwarding

```bash
sudo bash -c 'echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf'
sudo bash -c 'echo "net.ipv6.conf.all.forwarding=1" >> /etc/sysctl.conf'
sudo sysctl -p
```

### Generate server keys

```bash
wg genkey | sudo tee /etc/wireguard/server.key | wg pubkey | sudo tee /etc/wireguard/server.pub
sudo chmod 600 /etc/wireguard/server.key
```

### Deploy config

```bash
sudo cp 05-wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
```

Edit `/etc/wireguard/wg0.conf`:
- Replace `REPLACE_WITH_SERVER_PRIVATE_KEY` with the contents of `/etc/wireguard/server.key`
- Replace `REPLACE_WITH_PHONE_PUBLIC_KEY` with the phone's WireGuard public key

### Enable and start

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show   # verify: interface up, peer listed
```

### Phone client (WireGuard iOS — App Store)

| Field | Value |
| ----- | ----- |
| Server endpoint | `<WAN-IP>:51820` |
| DNS | `10.8.0.1` |
| Allowed IPs | `0.0.0.0/0` (IPv4 only — do NOT add `::/0`, see network-context.md "WireGuard IPv6 black hole") |
| On-Demand | Cellular + Wi-Fi enabled, no SSID exclusions |

The server public key comes from `/etc/wireguard/server.pub`. The phone's public key
(generated by the app) goes into `wg0.conf` as the peer `PublicKey`.

### Adding additional peers (macOS or other)

1. Use the **WireGuard Mac App Store app** — not Homebrew. See `05-wireguard/peer-template.conf`
   for a fully annotated config with common mistakes called out.
2. Assign the next free tunnel IP. `10.8.0.2`–`10.8.0.7` are in use; start at `10.8.0.8`.
3. Add a `[Peer]` block to `wg0.conf`: public key + `/32` AllowedIPs.
4. `sudo systemctl reload wg-quick@wg0` — no restart needed for adding peers.

### Verify

```bash
sudo wg show              # peers listed, recent handshake timestamps
ping 10.8.0.2             # phone responds when tunnel is active
```

On the peer, test in this order — each failure level points to a different problem:

```
ping 10.8.0.1    # tunnel up
ping 1.1.1.1     # NAT/forwarding working
ping google.com  # DNS working
```

See `network-context.md` "Peer onboarding — what not to do" for the failure table.

---

## Step 7: CAKE SQM (`06-cake/`)

CAKE (Common Applications Kept Enhanced) eliminates upload bufferbloat. Without it,
latency spikes to 400–800 ms under VPN upload load. With CAKE: 11 ms loaded vs 14 ms
idle (measured on Spectrum ~200/100 Mbps).

**Scope:** shapes `enp1s0` egress — all traffic the t630 forwards toward the router.
Covers upload bufferbloat for WireGuard VPN clients. Does not help general LAN device
download bufferbloat (those go directly through the Netgear).

### Install

```bash
sudo apt install -y iproute2   # tc is part of iproute2; already present on Ubuntu 24.04

sudo cp 06-cake/setup.sh /usr/local/sbin/cake-setup.sh
sudo chmod 755 /usr/local/sbin/cake-setup.sh
sudo cp 06-cake/cake.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cake
```

### Tune bandwidth cap

Open `06-cake/setup.sh` and adjust `UPLOAD_MBPS` to 90% of measured ISP upload.
Current value: `85` (90% of ~94 Mbps measured on Spectrum). Keep it below the ISP
ceiling so CAKE's queue fills before the modem's unmanaged FIFO.

### DNS priority marking

`cake-setup.sh` also installs two `iptables` mangle rules marking DNS response
packets (source port 53, UDP and TCP) with DSCP EF. CAKE's `diffserv4` scheduler
places them in the highest-priority tin — DNS answers skip bulk traffic, so every
new connection resolves before its first byte is transmitted.

### Verify

```bash
systemctl status cake
tc qdisc show dev enp1s0                                       # → cake bandwidth 85Mbit
sudo iptables -t mangle -L POSTROUTING -v | grep DSCP         # → two rules, sport 53 → EF
```

Live queue stats:
```bash
watch -n1 tc -s qdisc show dev enp1s0
```

---

## Step 8: Uptime Kuma (`07-uptime-kuma/`)

Uptime Kuma monitors every layer of the stack. Set it up after everything else exists
to monitor — the CAKE monitoring script especially depends on CAKE being installed.

```bash
mkdir -p ~/uptime-kuma
cp 07-uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d
```

Web UI at `http://192.168.1.118:3001`. Create an admin account on first run.
Data persists in `~/uptime-kuma/data/` (bind mount — back this directory up directly).

Uptime Kuma uses `network_mode: host`, placing it directly on the host network stack.
`127.0.0.1:5335` reaches Unbound on the host loopback — unlike Pi-hole (inside a
Docker bridge), which must use `172.17.0.1#5335`.

### DNS monitors

| Friendly Name | Type | Hostname | Resolver | Port | Record |
| --- | --- | --- | --- | --- | --- |
| Unbound – Basic | DNS | `cloudflare.com` | `127.0.0.1` | `5335` | A |
| Unbound – DNSSEC | DNS | `internetsociety.org` | `127.0.0.1` | `5335` | A |
| Pi-hole – Full Chain | DNS | `cloudflare.com` | `127.0.0.1` | `53` | A |
| Pi-hole – Web UI | TCP Port | `192.168.1.118` | — | `8080` | — |
| Home Router | HTTP(s) | `http://192.168.1.1` | — | — | — |

Enter the IP only in the resolver field — no port. Port goes in the separate Port
field. `127.0.0.1:5335` in the resolver field creates an invalid double-port and
causes intermittent failures.

### Packet loss monitors (Push type)

Create three Push monitors:

| Friendly Name | Heartbeat Interval | Retries |
| --- | --- | --- |
| Packet Loss – Router (LAN) | 60s | 2 |
| Packet Loss – Internet (1.1.1.1) | 60s | 2 |
| CAKE SQM | 90s | 2 |

After saving, copy each push URL token (strip `?status=…` from the end) into the
corresponding script below.

### Packet loss monitoring script

```bash
cp 07-uptime-kuma/packet-loss-monitor.sh ~/packet-loss-monitor.sh
chmod +x ~/packet-loss-monitor.sh
# Edit: fill in ROUTER_PUSH_URL and INTERNET_PUSH_URL tokens, confirm ROUTER_IP
nano ~/packet-loss-monitor.sh
# Test:
~/packet-loss-monitor.sh
# Both Push monitors should flip green within a few seconds. Then schedule:
crontab -e
```

Add to crontab:
```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

The script sends 50 pings per check (10 seconds) so it fits in the 60-second window.
Loss % is placed in the `ping` field so Uptime Kuma graphs it over time.

### CAKE monitoring script

```bash
cp 07-uptime-kuma/cake-monitor.sh ~/cake-monitor.sh
chmod +x ~/cake-monitor.sh
# Edit: fill in PUSH_URL token (strip the query string — keep only the base URL)
nano ~/cake-monitor.sh
# Test:
~/cake-monitor.sh
# Add to crontab (same session as above):
crontab -e
```

Add to crontab:
```
* * * * * /home/USERNAME/cake-monitor.sh
```

Set the CAKE SQM Push monitor heartbeat to **90s** — cron fires every 60s but
scheduling jitter can push the heartbeat to second 61–62; a 90s window absorbs that
without false "down" flaps.

**Packet loss threshold guidance:**

| Threshold | Meaning |
| --- | --- |
| 1–2% | Strict — catches early degradation |
| 5% | Standard — video calls start glitching |
| 10% | Lenient — things noticeably broken |
| 15% | Severe events only |

---

## Step 9: GPU Performance (`08-gpu-performance/`)

The Carrizo iGPU downclocks to ~200 MHz headless. This makes NoMachine unusable.
DNS is unaffected — skip this step if you only use SSH.

**Requires a reboot.** Do this before installing NoMachine.

### 1. Kernel parameters

Edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
```

- `amdgpu.runpm=0` — disables runtime power management (root cause of headless downclocking)
- `amdgpu.dpm=1` — keeps dynamic power management active
- `processor.max_cstate=1` — prevents deep CPU sleep, improves remote desktop latency

```bash
sudo update-grub && sudo reboot
```

### 2–4. Services and udev rule

```bash
sudo cp 08-gpu-performance/gpu-performance.service \
        08-gpu-performance/cpu-performance.service /etc/systemd/system/
sudo cp 08-gpu-performance/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance cpu-performance
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```

The udev rule is the critical piece. The systemd services fire once at boot. The udev
rule re-asserts `high` performance mode on every DRM event — catching display hotplug
and runtime PM transitions that would otherwise re-throttle the GPU mid-session.

### Verify

```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level   # → high
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u # → performance
```

---

## Step 10: Remote Desktop (`09-remote-desktop/`)

```bash
sudo apt install -y xubuntu-desktop xfce4 xfce4-goodies
sudo apt install -y cpufrequtils gamemode schedtool
```

**NoMachine** (primary, port 4000) — download `.deb` from https://www.nomachine.com/download:

```bash
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

## Step 11: Point LAN Clients at t630 (router — no repo files)

Do this **last**, after the full stack is verified. This is the step that makes
every device on your LAN use Pi-hole.

On the Netgear R7000: Basic → Internet Setup → Domain Name Server (DNS Address):
- Primary DNS: `192.168.1.118`
- Secondary DNS: `1.1.1.1` (resilience — if t630 goes down the network stays online,
  losing ad-blocking until t630 recovers)

Renew DHCP leases on all client devices. Verify on any client:
```
nslookup example.com   # Server field must show 192.168.1.118
```

---

## Verification checklist

Run these after completing all steps to confirm the full stack is operating:

- [ ] `systemctl status unbound` — active
- [ ] `dig @127.0.0.1 -p 5335 example.com +dnssec` — `ad` flag present (DNSSEC working)
- [ ] `dig @127.0.0.1 -p 5335 netflix.com +short` — resolves (Cloudflare DoT forward-path works end-to-end)
- [ ] `sudo unbound-control lookup netflix.com` → `forwarding request` to `1.1.1.1@853` / `1.0.0.1@853`
- [ ] `sudo unbound-control lookup chase.com` → iterative delegation (private, never forwarded)
- [ ] `docker ps` — pihole and uptime-kuma both Up and healthy
- [ ] Pi-hole web UI at `http://192.168.1.118:8080/admin/`
- [ ] Pi-hole Settings → DNS shows `172.17.0.1#5335` as the single custom upstream (no preset resolvers checked)
- [ ] `getent hosts security.ubuntu.com` — returns IP (host resolver working independently of Pi-hole)
- [ ] `sudo ufw status verbose` — all ports show `192.168.0.0/16` except 51820/udp which shows `Anywhere`
- [ ] `sudo wg show` — wg0 interface up, iPhone peer listed
- [ ] `systemctl status cake` — active
- [ ] `tc qdisc show dev enp1s0` — shows `cake` qdisc with `bandwidth 85Mbit`
- [ ] `sudo iptables -t mangle -L POSTROUTING -v | grep DSCP` — two rules marking sport 53 as EF
- [ ] `systemctl status unbound-cache-dump.timer` — active (waiting)
- [ ] Uptime Kuma at `http://192.168.1.118:3001` — all DNS monitors green
- [ ] Uptime Kuma: packet loss monitors receiving heartbeats every ~60s (`crontab -l` confirms jobs)
- [ ] Packet loss to gateway and 1.1.1.1 both below 1% under normal load
- [ ] Blocked domain (`doubleclick.net`) → `0.0.0.0` from a LAN client
- [ ] `cat /sys/class/drm/card*/device/power_dpm_force_performance_level` → `high`
- [ ] `nslookup example.com` from LAN client → server shows `192.168.1.118`

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persists hourly and restores at boot automatically
- Pi-hole named volumes backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data: back up `~/uptime-kuma/data/` directly
- Refresh root hints periodically: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`
- Re-run `sudo bash 04-ufw/setup.sh` any time firewall rules need to be reset (idempotent)
