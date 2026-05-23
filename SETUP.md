# Setup Guide

This document walks through how this DNS stack was built on the HP t630 thin client. It's both a reproduction guide and a record of the configuration decisions made along the way.

## Target hardware and OS

- HP t630 Mobile Thin Client
- AMD Carrizo APU (GX-420GI), 4 GB RAM, 16 GB eMMC
- Ubuntu 24.04.4 LTS, kernel 6.17 series
- Wired Ethernet to LAN

The t630 was chosen because it's silent, low-power (~10W idle), and inexpensive on the used market. The Carrizo APU has a quirk that needed remediation (see "GPU throttling" below) but is otherwise capable for this workload.

## Network role

The t630 sits on the LAN at a static address (assigned via DHCP reservation on the router). Client devices receive its address as their DNS server via DHCP option 6, set on the router.

## Part 1: Unbound (host)

Unbound runs directly on the host OS, not in a container. It serves recursive DNS on port 5335 to the Pi-hole container only — Pi-hole is the upstream-facing service.

### Install

```bash
sudo apt update
sudo apt install -y unbound
```

### Root hints

Unbound needs a current copy of the root server list:

```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
```

### DNSSEC trust anchor

```bash
sudo unbound-anchor -a /var/lib/unbound/root.key
sudo chown unbound:unbound /var/lib/unbound/root.key
```

The `auto-trust-anchor-file` directive in `root-auto-trust-anchor-file.conf` keeps this file updated automatically per RFC 5011.

### Drop in configuration

```bash
sudo cp unbound/*.conf /etc/unbound/unbound.conf.d/
sudo unbound-checkconf
sudo systemctl restart unbound
sudo systemctl enable unbound
```

### Verify

```bash
dig @127.0.0.1 -p 5335 example.com
dig @127.0.0.1 -p 5335 example.com +dnssec | grep -i "ad;"
```

The second command should show the `ad` (authenticated data) flag set, confirming DNSSEC validation is working.

### Configuration notes

Current configs are organized as Unbound drop-ins under `/etc/unbound/unbound.conf.d/`. They include some overlap across files (multiple `server:` sections with shared keys) — this works because Unbound merges drop-ins, but a future cleanup pass will consolidate them. See "Known issues" in the README.

Caching strategy: aggressive. `serve-expired: yes` with a 90-day expired-TTL means clients get instant responses from cache even when upstream is slow or unreachable, with background refresh. Cache sizes (512m rrset, 256m msg) are generous for a 4 GB host but well within budget given Unbound's actual memory use.

### Cache persistence

Unbound's in-memory cache is dumped to disk hourly and restored at boot, so warm-cache performance survives reboots.

**Install scripts:**
```bash
sudo cp scripts/unbound-cache-dump scripts/unbound-cache-load /usr/local/bin/
sudo chmod +x /usr/local/bin/unbound-cache-dump /usr/local/bin/unbound-cache-load
sudo mkdir -p /var/lib/unbound/cache
```

**Install drop-in and units:**
```bash
sudo mkdir -p /etc/systemd/system/unbound.service.d/
sudo cp systemd/unbound.service.d/override.conf /etc/systemd/system/unbound.service.d/
sudo cp systemd/unbound-cache-dump.timer systemd/unbound-cache-dump.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now unbound-cache-dump.timer
```

The drop-in (`override.conf`) hooks `unbound-cache-load` into Unbound's start sequence (2 s after start, to let the socket settle) and `unbound-cache-dump` into its stop. The timer provides an additional hourly dump independent of service restarts.

**Verify:**
```bash
systemctl status unbound-cache-dump.timer
# Should show active (waiting); NEXT trigger ~10 min after boot
```

## Part 2: Pi-hole (Docker)

Pi-hole runs as a single container with named volumes for persistence.

### Install Docker

```bash
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for the group change to apply
```

### Configure and start Pi-hole

```bash
cd pihole/
# Edit docker-compose.yml — set WEBPASSWORD to a real value
# Confirm PIHOLE_DNS_ points to your Unbound (see "Upstream DNS resolution" below)
docker compose up -d
docker compose logs -f pihole  # watch startup, Ctrl-C when healthy
```

### First-time web access

Visit `http://<t630-ip>:8080/admin/` and log in with the password you set.

### Upstream DNS resolution

The compose file has `PIHOLE_DNS_=127.0.0.1#5335` as committed. This is the configuration that came off the running container, but it implies Unbound is reachable inside the container — which it isn't, since Unbound runs on the host. The likely correct value for this architecture is `172.17.0.1#5335`, which routes from the container to the Docker bridge gateway, which is the host.

If queries are slow or failing on first deployment, change to:
```yaml
PIHOLE_DNS_: "172.17.0.1#5335"
```
and recreate the container with `docker compose up -d`.

To verify Unbound is being used, watch the Unbound query log while issuing a query from a client, or use `dig` from the host:
```bash
dig @<t630-ip> example.com
# Should be answered; check Pi-hole's Query Log to see the upstream marked as 127.0.0.1#5335 or 172.17.0.1#5335
```

### Firewall

If UFW is enabled on the host, open the required ports:
```bash
sudo ufw allow 53/tcp
sudo ufw allow 53/udp
sudo ufw allow 8080/tcp   # Pi-hole web UI; restrict to LAN if exposed
```

## Part 3: GPU throttling remediation (Carrizo-specific)

The AMD Carrizo APU in the t630 aggressively downclocks its iGPU when no display is detected. This isn't a DNS problem — DNS doesn't touch the GPU — but it cripples NoMachine remote desktop, which made administering the box painful. If you administer the t630 exclusively via SSH, skip this section.

### Symptoms

- NoMachine sessions visibly freeze and stutter
- `cat /sys/class/drm/card*/device/pp_dpm_sclk` shows the GPU pinned at the lowest power state (200 MHz) even when active

### Four-part fix

**1. Kernel boot parameters** — edit `/etc/default/grub`:
GRUB_CMDLINE_LINUX_DEFAULT="quiet amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1"
Then `sudo update-grub` and reboot.

- `amdgpu.dpm=1` keeps dynamic power management on
- `amdgpu.runpm=0` disables runtime PM, which is what was unloading the GPU when no display was connected
- `processor.max_cstate=1` keeps the CPU out of deep sleep states (also helps NoMachine responsiveness)

**2. Systemd service** (`systemd/gpu-performance.service`) — copy in:
```bash
sudo cp systemd/gpu-performance.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-performance.service
```
This forces the GPU to `high` performance level at boot.

**3. Systemd service** (`systemd/cpu-performance.service`) — copy in:
```bash
sudo cp systemd/cpu-performance.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cpu-performance.service
```
This forces all CPU cores to the `performance` scaling governor at boot, preventing the kernel from downclocking the CPU when load is low.

**4. Udev rule** (`udev/99-amdgpu-performance.rules`) — copy in:
```bash
sudo cp udev/99-amdgpu-performance.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=drm
```
The rule re-asserts `high` on any DRM subsystem event. This is the critical piece — the systemd service alone fires once at boot, but later events (display hotplug, runtime PM transitions, suspend/resume) re-trigger the kernel's headless detection and re-throttle the GPU. The udev rule catches those events.

### Verify

```bash
cat /sys/class/drm/card*/device/power_dpm_force_performance_level
# Should output: high

cat /sys/class/drm/card*/device/pp_dpm_sclk
# Should show pstate 7 (highest, ~626 MHz) marked with *
```

If the card index changes across kernel updates (card0 vs card1), the glob in the service ExecStart and the wildcard in the udev rule both handle it.

## Part 4: Point clients at the t630

On your router's DHCP server, set DNS option 6 to the t630's static address. Renew DHCP leases on client devices, or reboot them. Verify on a client:

```bash
nslookup example.com
# Server should be the t630's address
```

## Verification checklist

After everything is up:

- [ ] `systemctl status unbound` — active, running
- [ ] `dig @127.0.0.1 -p 5335 example.com +dnssec` — answers with `ad` flag
- [ ] `docker ps` — Pi-hole container shows `Up X (healthy)`
- [ ] Pi-hole web UI loads at `http://<t630-ip>:8080/admin/`
- [ ] Pi-hole dashboard shows incoming queries from client IPs
- [ ] A blocked domain (try `doubleclick.net`) resolves to `0.0.0.0` from a client
- [ ] `cat /sys/class/drm/card*/device/power_dpm_force_performance_level` — high (if you applied GPU fix)

## Operational notes

- Pi-hole's blocklists update weekly by default via cron inside the container
- Unbound's DNS cache is persisted to disk hourly and restored at boot; see the cache persistence section in Part 1
- The named Docker volumes (`pihole_data`, `dnsmasq_data`) persist all Pi-hole state across container recreations — backup is just `docker run --rm -v pihole_data:/data busybox tar czf - /data > pihole-backup.tar.gz`
