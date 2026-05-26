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
(`7C:D3:0A:77:93:AE`) in the router's LAN setup. This gives the t630 a stable
address without a static IP on the OS side.

**DNS for LAN clients:** Set the router's primary DNS to `192.168.1.118` (the t630)
and secondary to `1.1.1.1`. On the Netgear R7000 this is under Basic → Internet
Setup → Domain Name Server. The router pushes these values to DHCP clients, so
every device on the LAN sends queries directly to Pi-hole — Pi-hole sees individual
client IPs, enabling per-device statistics.

The `1.1.1.1` secondary is a resilience choice: if the t630 goes down the network
stays online, losing ad-blocking until the t630 recovers. Removing it would take
the entire network offline on t630 reboots.

**WireGuard port forwarding (for VPN — Part 9):** In the Netgear R7000 under
Advanced → Advanced Setup → Port Forwarding / Port Triggering, add a rule:
- Service: WireGuard (or custom)
- Protocol: UDP
- External port: 51820
- Internal IP: 192.168.1.118
- Internal port: 51820

This is required for the phone to reach the VPN from outside the LAN.

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

---

## Part 5: Firewall

```bash
sudo bash ufw/setup.sh
```

All services LAN-only (`192.168.0.0/16`): DNS 53, Unbound 5335, Pi-hole UI 8080,
Uptime Kuma 3001, SSH 22, xrdp 3389, NoMachine 4000, mDNS 5353.

The script resets and rebuilds all rules from scratch — safe to re-run.

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

---

## Part 9: WireGuard VPN (full tunnel for iPhone)

All phone traffic routes through the t630 when connected. DNS goes to Pi-hole →
Unbound, so ad-blocking and DNSSEC work away from home. Requires the router port
forwarding rule in Part 0 and a static public IP.

### Install and configure

```bash
sudo bash wireguard/setup.sh
```

The script:
1. Installs `wireguard-tools` and `qrencode`
2. Generates server and client keypairs
3. Writes `/etc/wireguard/wg0.conf` (server) and `/etc/wireguard/ios-client.conf`
4. Enables `net.ipv4.ip_forward` persistently via `/etc/sysctl.d/99-wireguard.conf`
5. Enables and starts `wg-quick@wg0`
6. Prints the client config and a QR code to scan

### Import to iPhone

1. Install the **WireGuard** app from the App Store
2. Tap **+** → **Create from QR code**
3. Scan the QR code printed by the setup script
4. Toggle the tunnel on — all traffic now routes through the t630

### Re-run UFW after WireGuard setup

If you run Part 5 (firewall) after Part 9, re-run it to restore the WireGuard UFW
rules (the script is idempotent):

```bash
sudo bash ufw/setup.sh
```

### Add a second peer (optional)

Add another `[Peer]` block to `/etc/wireguard/wg0.conf` and reload:

```bash
# Generate a new keypair on the t630
CLIENT2_PRIVATE=$(wg genkey)
CLIENT2_PUBLIC=$(echo "$CLIENT2_PRIVATE" | wg pubkey)
echo "Public: $CLIENT2_PUBLIC"
# Add to wg0.conf, then:
sudo wg set wg0 peer "$CLIENT2_PUBLIC" allowed-ips 10.8.0.3/32
sudo wg-quick save wg0
```

### Management commands

```bash
sudo wg show                     # status and peer handshake times
sudo systemctl restart wg-quick@wg0
sudo journalctl -u wg-quick@wg0 -f
```

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
- [ ] `sudo ufw status verbose` — LAN ports show `192.168.0.0/16`; only `51820/udp` says `Anywhere`
- [ ] `systemctl status unbound-cache-dump.timer` — active (waiting)
- [ ] `systemctl status wg-quick@wg0` — active (if WireGuard deployed)
- [ ] `sudo wg show` — peer handshake time recent when phone is connected

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persists hourly and restores at boot automatically
- Pi-hole named volumes backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data: back up `~/uptime-kuma/data/` directly
- Refresh root hints periodically: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`

