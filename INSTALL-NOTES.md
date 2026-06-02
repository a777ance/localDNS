# Fresh Install Simulation — Known Issues and Break Points

Results of a full walkthrough of the setup guide against the actual config files in
this repo, simulating a fresh Ubuntu 24.04 install on identical hardware (HP t630).
Every point of breakage, confusion, or security risk is catalogued below with its
severity and fix. See the summary table at the bottom for a quick reference.

---

## BLOCKERS — will stop a fresh install cold

### 1. No `git clone` step in the setup guide

**Location:** README.md, top of Setup section

**What breaks:** Every `cp` command in the setup guide uses relative paths
(`01-unbound/*.conf`, `06-cake/setup.sh`, etc.). Without first cloning the repo to
the t630 and `cd`-ing into it, every single one of those commands fails with
"No such file or directory" — before a single service is configured.

**Fix (now applied):** README.md now opens the Setup section with an explicit clone step.

---

### 2. `wg0.conf` fails to parse — WireGuard will not start

**Location:** `05-wireguard/wg0.conf`

Two problems in the repo file cause `wg-quick@wg0.service` to fail at parse time:

**Problem A — empty `[Peer]` block (Mac peer):**

```
[Peer]
# Mac peer — added via WireGuard macOS (App Store, NOT Homebrew)
# PublicKey = REPLACE_WITH_MAC_PUBLIC_KEY
# AllowedIPs = 10.8.0.7/32
```

The `[Peer]` section header was uncommented but both required fields were commented
out. `wg-quick` encountering a `[Peer]` block with no `PublicKey` errors out:
"A peer is missing a public key."

**Problem B — invalid placeholder key (laptop peer):**

```
PublicKey = REPLACE_WITH_LAPTOP_PUBLIC_KEY
```

`REPLACE_WITH_LAPTOP_PUBLIC_KEY` is not valid base64. `wg` fails with an invalid key
decode error.

The setup instructions only tell you to replace the server private key and the phone
public key — they say nothing about fixing the Mac and laptop peer blocks. An installer
following the guide literally would hit `wg-quick@wg0.service` failing to start with
no obvious reason.

**Fix (now applied):** The Mac `[Peer]` header is now commented out alongside its
body. The laptop `PublicKey` line is commented out with an explicit warning. README.md
now has an explicit "fix the peer blocks before deploying" instruction.

---

## HIGH — will cause significant confusion or debugging time

### 3. Host DNS breaks between Steps 3 and 4 and the warning is in the wrong place

**Location:** README.md, Steps 3–4

When `docker compose up -d` succeeds and Pi-hole starts, Docker's proxy process binds
`0.0.0.0:53` — including `127.0.0.53`, the address systemd-resolved's stub listener
uses. Host DNS breaks immediately. Any diagnostic command you naturally try next
(`docker compose logs`, `apt`, `curl`) fails with "Temporary failure in name
resolution."

The original SETUP.md warned "Do this immediately after Pi-hole starts" but placed
the warning *after* the `docker compose up -d` command. A first-time installer will
almost certainly try `docker compose logs -f pihole` next, get stuck, and not
understand why.

**Fix (now applied):** README.md merges Steps 3 and 4 into a single combined block
with the warning placed *before* `docker compose up -d`. The sequence is: edit the
compose file → start Pi-hole → fix host DNS (no other commands in between).

---

### 4. `WEBPASSWORD: "CHANGE_ME"` — easy to overlook, starts Pi-hole with a known password

**Location:** `02-pihole/docker-compose.yml`

The compose file is committed with `WEBPASSWORD: "CHANGE_ME"`. If an installer runs
`docker compose up -d` without editing it first, Pi-hole starts with a
publicly-known credential. The old guide flagged it as a note in running prose —
easy to skim past when following step-by-step instructions.

**Fix (now applied):** README.md makes changing the password the first sub-step of
the Pi-hole section, before the `docker compose up -d` command.

---

## MEDIUM — silent or hard-to-diagnose failures

### 5. Monitoring script placeholder tokens cause silent `curl` failures

**Location:** `07-uptime-kuma/packet-loss-monitor.sh`, `07-uptime-kuma/cake-monitor.sh`

Both scripts ship with placeholder push tokens:
- `<PUSH_TOKEN_ROUTER>`, `<PUSH_TOKEN_INTERNET>` in `packet-loss-monitor.sh`
- `<PUSH_TOKEN_CAKE>` in `cake-monitor.sh`

`curl` requests to URLs containing literal `<>` fail. All output is redirected to
`/dev/null`, so there is no visible error. The cron jobs fire every minute
indefinitely, and the Uptime Kuma monitors never go green. Nothing in the system
logs tells you why.

**Fix (now applied):** README.md adds an explicit manual test step — run each script
once by hand and confirm the Uptime Kuma monitor flips green *before* adding it to
crontab.

---

### 6. Crontab `USERNAME` placeholder must be replaced manually

**Location:** README.md / SETUP.md crontab instructions

```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

Copying this literally into crontab creates a job that runs a path that doesn't exist.
No obvious error — `cron` just logs "command not found" to syslog.

**Fix (now applied):** README.md replaces `USERNAME` with `USER` and adds a reminder
to substitute the actual username.

---

### 7. UFW INPUT rules do not restrict Pi-hole's published port 53

**Location:** `04-ufw/setup.sh`

Docker inserts DNAT rules into the `DOCKER` iptables chain, which is processed
*before* UFW's INPUT chain. Pi-hole port 53 (published via `ports: "53:53/udp"` in
the compose file) bypasses UFW's `from 192.168.0.0/16` restriction entirely. The
`ufw allow in from "$LAN" to any port 53` rules in `setup.sh` apply to host-resident
services — they don't gate Docker-published ports.

In practice this is safe for the current topology: the Netgear R7000 NATs all WAN
traffic and only forwards 51820/UDP to the t630, so the external boundary is the
router. But it means UFW does not provide the LAN-restriction layer for Pi-hole port
53 that the comments in `setup.sh` imply. Internal LAN isolation for port 53 relies
entirely on the router.

**Fix:** Document this accurately. README.md now includes a note in the UFW step.
Unbound on port 5335 is correctly protected by UFW (it is a host-resident service, not
Docker-published) via the `ufw allow in on docker0 to any port 5335` rule.

---

## MINOR — cosmetic or low-impact

### 8. `server.conf` indentation inconsistency

**Location:** `01-unbound/server.conf`, line 6

The `interface:` line has 6 spaces of indentation while all other lines have 4.
Unbound's parser is whitespace-insensitive so this is harmless, but it looks wrong.

**Fix (now applied):** Corrected to 4 spaces.

---

### 9. `sysctl.conf` append is not idempotent

**Location:** SETUP.md Step 6 (now README.md Step 6)

The original command:
```bash
sudo bash -c 'echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf'
```

Appends to `/etc/sysctl.conf` every time it runs. Running the step twice creates
duplicate lines. Functionally harmless (the last value wins) but bad practice.

**Fix (now applied):** README.md now uses a dedicated drop-in file:
```bash
printf 'net.ipv4.ip_forward=1\nnet.ipv6.conf.all.forwarding=1\n' \
  | sudo tee /etc/sysctl.d/99-wireguard-forward.conf
sudo sysctl --system
```
This is idempotent and follows the proper `sysctl.d` pattern for Ubuntu.

---

### 10. GRUB edit shows the target string but not a safe append command

**Location:** README.md Step 9

Showing the desired final value of `GRUB_CMDLINE_LINUX_DEFAULT` without showing how
to get there safely invites someone to copy the line verbatim and overwrite existing
kernel flags (`quiet splash`, or custom power management parameters they may have set).

**Fix (now applied):** README.md now shows an explicit "append to whatever is
already there" instruction with a before/after example.

---

### 11. MAC address not mentioned in Step 0

**Location:** README.md Step 0

DHCP reservation requires the t630's MAC address. On a fresh install the MAC is
on a label on the device or in the router's current lease table — but a first-time
installer may not know where to find it in the OS.

**Fix (now applied):** README.md adds `ip link show enp1s0` (the `link/ether` value)
as the first sub-step of Step 0.

---

### 12. Cache dump correctness depends on Ubuntu's base unbound unit having no `ExecStop`

**Location:** `01-unbound/unbound.service.d/override.conf`

`override.conf` adds `ExecStop=/usr/local/bin/unbound-cache-dump`. Systemd runs
`ExecStop` commands before sending SIGTERM to the main process, so `unbound-control
dump_cache` can still talk to a running Unbound. This is correct — *provided* the
base `unbound.service` unit on Ubuntu has no explicit `ExecStop` of its own. On
Ubuntu 24.04 LTS, the base unit uses SIGTERM and has no `ExecStop`: the assumption
holds.

A future distro update that adds `ExecStop=/usr/sbin/unbound-control stop` to the
base unit would silently break cache dumps on every shutdown — the base ExecStop
would fire first, shut Unbound down, and the dump script would then fail to connect.

**Mitigation:** Monitor Ubuntu's `unbound` package changelogs when upgrading. If the
base unit ever gains an explicit stop command, migrate the dump to `ExecStopPost`
or reset the `ExecStop=` list in the override before redefining it.

---

## Summary

| # | Severity | Location | Impact |
|---|----------|----------|--------|
| 1 | **BLOCKER** | README.md preamble | No `git clone` — all `cp` commands fail immediately |
| 2 | **BLOCKER** | `05-wireguard/wg0.conf` | Malformed peer blocks — `wg-quick@wg0.service` fails to parse |
| 3 | High | README.md Steps 3–4 | Host DNS breaks silently; warning was in the wrong place |
| 4 | High | `02-pihole/docker-compose.yml` | Known-weak default password easy to miss in prose |
| 5 | Medium | `07-uptime-kuma/*.sh` | Silent `curl` failures when push tokens not replaced |
| 6 | Medium | README.md Step 8 | `USERNAME` crontab placeholder creates broken cron job |
| 7 | Medium | `04-ufw/setup.sh` | UFW port 53 restriction ineffective for Docker-published ports |
| 8 | Minor | `01-unbound/server.conf` | Indentation inconsistency on `interface:` line |
| 9 | Minor | README.md Step 6 | `sysctl.conf` append not idempotent |
| 10 | Minor | README.md Step 9 | GRUB edit guidance incomplete — risk of clobbering existing flags |
| 11 | Minor | README.md Step 0 | No guidance on finding the MAC address |
| 12 | Minor | `unbound.service.d/override.conf` | Cache dump assumes base unit has no `ExecStop` |
