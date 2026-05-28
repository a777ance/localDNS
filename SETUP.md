# Setup Guide

Full reproduction walkthrough for the localDNS stack on the HP t630 thin client.

## Hardware and OS

- HP t630 (AMD Carrizo GX-420GI quad-core, 4 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Ethernet (enp1s0), Wi-Fi disabled

## Part 0: Router prerequisites

Before touching the t630, configure the router so the t630 has a stable address
and the network is ready to use it as DNS.

**DHCP reservation:** Reserve `192.168.1.118` for the t630's MAC address
(`<T630-MAC>`) in the router's LAN setup. This gives the t630 a stable
address without a static IP on the OS side.

**DNS for LAN clients:** Set the router's primary DNS to `192.168.1.118` (the t630)
and secondary to `1.1.1.1`. On the Netgear R7000 this is under Basic → Internet
Setup → Domain Name Server. The router pushes these values to DHCP clients, so
every device on the LAN sends queries directly to Pi-hole — Pi-hole sees individual
client IPs, enabling per-device statistics.

The `1.1.1.1` secondary is a resilience choice: if the t630 goes down the network
stays online, losing ad-blocking until the t630 recovers. Removing it would take
the entire network offline on t630 reboots.

See `docs/network-context.md` for full router setting rationale.

---

## Part 1: Unbound

Unbound runs on the host OS, not in a container. It serves recursive DNS on port
5335 to the Pi-hole container only.

### Install

```bash
sudo apt update && sudo apt install -y unbound
```

### Root hints and DNSSEC anchor

```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
sudo unbound-anchor -a /var/lib/unbound/root.key
sudo chown unbound:unbound /var/lib/unbound/root.key
```

### Drop in configuration

```bash
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo unbound-checkconf
sudo systemctl enable --now unbound
```

Four drop-ins: `server.conf` (network/security), `tuning.conf` (performance, TTLs,
serve-expired — single source of truth for all caching values),
`remote-control.conf` (Unix socket), `root-auto-trust-anchor-file.conf` (DNSSEC).

### Verify

```bash
dig @127.0.0.1 -p 5335 example.com +dnssec | grep "ad;"
# 'ad' flag = DNSSEC validation working
```

### Cache persistence

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

Cache is dumped hourly and on Unbound stop; restored 2 seconds after Unbound starts
(to let the socket settle). Warm-cache performance survives reboots.

---

## Part 2: Docker CE

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

## Part 3: Pi-hole

```bash
cd pihole/
# Set WEBPASSWORD before starting
docker compose up -d
docker compose logs -f pihole   # Ctrl-C when healthy
```

Web UI at `http://192.168.1.118:8080/admin/`.

### Set the upstream DNS in the Pi-hole UI

The compose file sets `PIHOLE_DNS_=127.0.0.1#5335` as the initial value. This is
wrong for the Docker bridge architecture — inside the container `127.0.0.1` is the
container's own loopback, not the host. After the container starts:

1. Go to Settings → DNS
2. Remove `127.0.0.1#5335` from the custom upstream field
3. Enter `172.17.0.1#5335` — the Docker bridge gateway (host as seen from container)
4. Click Save & Apply

This value persists in the `pihole_data` Docker volume across container restarts.
The compose env var is only read on first creation of a fresh volume.

### Interface setting: "Permit all origins"

Pi-hole's Settings → DNS shows "Permit all origins" as a potentially dangerous
option. It is safe here because UFW restricts port 53 to `192.168.0.0/16` — Pi-hole
cannot receive queries from outside the LAN regardless of this setting. "Permit all
origins" is the correct choice when the firewall handles the network boundary,
because it allows queries from Docker containers and bridged interfaces.

---

## Part 4: Uptime Kuma

```bash
mkdir -p ~/uptime-kuma
cp uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d
```

Web UI at `http://192.168.1.118:3001`. Create an admin account on first run.
Data persists in `~/uptime-kuma/data/` (bind mount — back this directory up directly).

### Monitor configuration

Add these monitors after first login. They provide layered DNS visibility and
packet loss tracking. See network-context.md "Uptime Kuma monitors" for the
diagnostic logic behind each one.

**DNS monitors (test query resolution, not just port availability)**

| Friendly Name | Type | Hostname | Resolver | Port | Record |
| --- | --- | --- | --- | --- | --- |
| Unbound – Basic | DNS | `cloudflare.com` | `127.0.0.1` | `5335` | A |
| Unbound – DNSSEC | DNS | `internetsociety.org` | `127.0.0.1` | `5335` | A |
| Pi-hole – Full Chain | DNS | `cloudflare.com` | `127.0.0.1` | `53` | A |
| Pi-hole – Web UI | TCP Port | `192.168.1.118` | — | `8080` | — |
| Home Router | HTTP(s) | `http://192.168.1.1` | — | — | — |

For the resolver field: enter the IP only, **no port**. Port goes in the
separate Port field. `127.0.0.1:5335` in the resolver field is wrong — it
creates an invalid double-port and causes intermittent failures.

**Packet loss monitors (Push type)**

Create two Push monitors:

| Friendly Name | Heartbeat Interval | Retries |
| --- | --- | --- |
| Packet Loss – Router (LAN) | 60s | 2 |
| Packet Loss – Internet (1.1.1.1) | 60s | 2 |

After saving each, copy the push URL (token only, strip `?status=…` from
the end) into `scripts/packet-loss-monitor.sh`.

### Packet loss monitoring script

```bash
cp scripts/packet-loss-monitor.sh ~/packet-loss-monitor.sh
chmod +x ~/packet-loss-monitor.sh
# Edit: fill in ROUTER_PUSH_URL and INTERNET_PUSH_URL tokens, confirm ROUTER_IP
nano ~/packet-loss-monitor.sh
# Test manually:
~/packet-loss-monitor.sh
# Both Push monitors should flip green within a few seconds.
# Then schedule:
crontab -e
```

Add to crontab:
```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

The script sends 50 pings per check (10 seconds) so it fits comfortably in
the 60-second window. Loss % is placed in the `ping` field so Uptime Kuma
graphs it over time. `status=down` fires when loss exceeds `THRESHOLD`
(default 15% — lower to 5% once router hardware is stable).

**Threshold guidance:**

| Threshold | Meaning |
| --- | --- |
| 1–2% | Strict — catches early degradation |
| 5% | Standard — video calls start glitching |
| 10% | Lenient — things noticeably broken |
| 15% | Severe events only — router-is-overheating tier |

---

## Part 5: Firewall

```bash
sudo bash ufw/setup.sh
```

All services LAN-only (`192.168.0.0/16`): DNS 53, Unbound 5335, Pi-hole UI 8080,
Uptime Kuma 3001, SSH 22, xrdp 3389, NoMachine 4000, mDNS 5353.

Port 51820/UDP (WireGuard) is open to Anywhere — the phone connects from cellular
and cannot be LAN-restricted. This is the single intended exception.

The script resets and rebuilds all rules from scratch — safe to re-run.

---

## Part 5a: WireGuard VPN

WireGuard tunnels peers back to the home network from anywhere on cellular or
untrusted Wi-Fi. DNS goes through Pi-hole, so ad-blocking and DNSSEC work
identically on cellular.

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
sudo cp wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
```

Edit `/etc/wireguard/wg0.conf`:
- Replace `REPLACE_WITH_SERVER_PRIVATE_KEY` with the contents of `/etc/wireguard/server.key`
- Replace `REPLACE_WITH_PHONE_PUBLIC_KEY` with the phone's WireGuard public key

### UFW and forwarding

`setup.sh` already sets `ufw default allow routed`. This is required —
without it, the UFW FORWARD chain drops peer traffic even when the tunnel is
up and handshaking. Do not add raw `iptables -A FORWARD` rules to wg0.conf
as a workaround; they land after UFW's DROP rule and are silently ignored.
See network-context.md "UFW + WireGuard forwarding" for the full failure
analysis.

### Enable and start

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show   # verify interface up, peer listed
```

### Phone client (WireGuard iOS — App Store)

Create a tunnel in the WireGuard iOS app with:

| Field | Value |
| ----- | ----- |
| Server endpoint | `<WAN-IP>:51820` |
| DNS | `10.8.0.1` |
| Allowed IPs | `0.0.0.0/0, ::/0` |
| On-Demand | Cellular + Wi-Fi enabled, no SSID exclusions |

The server public key comes from `/etc/wireguard/server.pub` on the t630.
The phone's public key (generated by the app) goes into wg0.conf as the peer `PublicKey`.

### Adding additional peers (macOS or other)

1. Use the **WireGuard Mac App Store app** — not Homebrew. See
   `wireguard/peer-template.conf` for a fully annotated config with common
   mistakes called out.
2. Assign the next available IP (10.8.0.7, 10.8.0.8, …).
3. Add a `[Peer]` block to wg0.conf on the server: public key + `/32` AllowedIPs.
4. `sudo systemctl reload wg-quick@wg0` (no restart needed for adding peers).

### Verify

```bash
sudo wg show            # peers listed, recent handshake timestamps
ping 10.8.0.2           # phone responds when tunnel active
```

On any peer: open WireGuard app → tap tunnel name → Transfer counters must
increment while browsing (not just "Connected"). Then test in order:

```
ping 10.8.0.1    # tunnel up
ping 1.1.1.1     # NAT/forwarding working
ping google.com  # DNS working
```

Each failure level points to a different problem. See network-context.md
"Peer onboarding — what not to do" for the failure table.

---

## Part 6: GPU throttling remediation (Carrizo-specific)

The Carrizo iGPU downclocks to ~200 MHz with no display attached, making NoMachine
unusable. DNS is unaffected — skip this section if you only use SSH.

**1. Kernel parameters** — edit `/etc/default/grub`:
GRUB_CMDLINE_LINUX_DEFAULT="quiet amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
- `amdgpu.runpm=0` — disables runtime power management (the cause of headless downclocking)
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

The udev rule is the critical piece. The systemd services fire once at boot.
The udev rule re-asserts `high` performance mode on every DRM subsystem event —
catching display hotplug and runtime PM transitions that would otherwise re-throttle
the GPU mid-session.

Verify:

```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # → high
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u  # → performance
```

---

## Part 7: Remote desktop

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

## Part 8: Point clients at the t630

Set the router's primary DNS to `192.168.1.118` (see Part 0). Renew DHCP leases.
Verify on a client: `nslookup example.com` — server should show `192.168.1.118`.


## Part 9: Uptime Kuma — Observability

See Part 4 for full monitor configuration. Summary of what's monitored and why
`127.0.0.1` works for DNS monitors:

Uptime Kuma uses `network_mode: host`, placing it directly on the host network
stack. `127.0.0.1:5335` reaches Unbound on the host loopback — the same address
any host process would use. This is unlike Pi-hole (inside a Docker bridge), which
must use `172.17.0.1#5335` to reach the host.

---

## Verification checklist

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
- [ ] `systemctl status unbound-cache-dump.timer` — active (waiting)
- [ ] Uptime Kuma: all DNS monitors green (Unbound-Basic, Unbound-DNSSEC, Pi-hole-FullChain)
- [ ] Uptime Kuma: packet loss monitors receiving heartbeats every ~60s (`crontab -l` confirms job is set)
- [ ] Packet loss to gateway and 1.1.1.1 both below 1% under normal (non-streaming) load

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persists hourly and restores at boot automatically
- Pi-hole named volumes backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data: back up `~/uptime-kuma/data/` directly
- Refresh root hints periodically: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`

