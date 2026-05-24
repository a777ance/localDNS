# Setup Guide

Full reproduction walkthrough for the localDNS stack on the HP t630 thin client.

## Hardware and OS

- HP t630 (AMD Carrizo GX-420GI quad-core, 4 GB RAM, 16 GB eMMC)
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Ethernet (enp1s0) at 192.168.1.118 via DHCP reservation on the router

## Part 1: Unbound

Unbound runs on the host OS (not in a container). It serves recursive DNS on port 5335.

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

Config files: `server.conf` (network/security), `tuning.conf` (performance, TTLs, serve-expired), `remote-control.conf` (Unix socket), `root-auto-trust-anchor-file.conf` (DNSSEC).

### Verify

```bash
dig @127.0.0.1 -p 5335 example.com +dnssec | grep -i "ad;"
# Should show the 'ad' flag — DNSSEC validation working
```

### Cache persistence

Unbound's cache is dumped hourly and restored at boot.

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
# Set WEBPASSWORD to a real value before starting
docker compose up -d
docker compose logs -f pihole   # Ctrl-C when healthy
```

Web UI at `http://192.168.1.118:8080/admin/`.

**Upstream DNS note:** `PIHOLE_DNS_=127.0.0.1#5335` is the committed value and works in production. If queries fail on first deployment, try `172.17.0.1#5335` (Docker bridge gateway) and run `docker compose up -d` again.

---

## Part 4: Uptime Kuma

```bash
mkdir -p ~/uptime-kuma
cp uptime-kuma/docker-compose.yml ~/uptime-kuma/
cd ~/uptime-kuma && docker compose up -d
```

Web UI at `http://192.168.1.118:3001`. Create an admin account on first run.

---

## Part 5: Firewall

```bash
sudo bash ufw/setup.sh
```

All services are LAN-only (`192.168.0.0/16`): DNS (53), Unbound (5335), Pi-hole UI (8080), Uptime Kuma (3001), SSH (22), xrdp (3389), NoMachine (4000), mDNS (5353).

---

## Part 6: GPU throttling remediation (Carrizo-specific)

The Carrizo iGPU downclocks aggressively with no display attached, making NoMachine unusable. Skip if you only use SSH.

**1. Kernel parameters** — edit `/etc/default/grub`:

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
```

```bash
sudo update-grub && sudo reboot
```

**2–4. Systemd services and udev rule:**

```bash
sudo cp systemd/gpu-performance.service systemd/cpu-performance.service /etc/systemd/system/
sudo cp udev/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance cpu-performance
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```

Verify:

```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # → high
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u  # → performance
```

---

## Part 7: Remote desktop

**Desktop environment:**

```bash
sudo apt install -y xubuntu-desktop xfce4 xfce4-goodies
```

**NoMachine** (primary, port 4000):

Download `.deb` from https://www.nomachine.com/download

```bash
sudo dpkg -i nomachine_*.deb
sudo cp nomachine/server.cfg /usr/NX/etc/server.cfg
sudo /usr/NX/bin/nxserver --restart
```

**xrdp** (RDP fallback, port 3389):

```bash
sudo apt install -y xrdp
sudo systemctl enable --now xrdp
```

**x2goserver** (low-bandwidth alternative):

```bash
sudo apt install -y x2goserver x2goserver-xsession
```

**Performance packages:**

```bash
sudo apt install -y cpufrequtils gamemode schedtool
```

---

## Part 8: Point clients at the t630

On your router, set DHCP option 6 (DNS) to `192.168.1.118`. Renew leases on clients.

```bash
nslookup example.com   # Server should show 192.168.1.118
```

---

## Verification checklist

- [ ] `systemctl status unbound` — active
- [ ] `dig @127.0.0.1 -p 5335 example.com +dnssec` — `ad` flag present
- [ ] `docker ps` — pihole and uptime-kuma both healthy
- [ ] Pi-hole UI loads at `http://192.168.1.118:8080/admin/`
- [ ] Uptime Kuma loads at `http://192.168.1.118:3001`
- [ ] Blocked domain (`doubleclick.net`) resolves to `0.0.0.0` from a client
- [ ] `cat /sys/class/drm/card*/device/power_dpm_force_performance_level` → `high`
- [ ] `sudo ufw status verbose` — all ports LAN-restricted

---

## Operational notes

- Pi-hole blocklists update weekly via cron inside the container
- Unbound cache persisted hourly; restored at boot automatically
- Pi-hole data in named Docker volumes (`pihole_data`, `dnsmasq_data`) — backup: `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
- Uptime Kuma data in `~/uptime-kuma/data/` — back up that directory directly
- Refresh root hints periodically: `sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && sudo systemctl restart unbound`
