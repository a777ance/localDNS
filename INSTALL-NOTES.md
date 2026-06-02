# Fresh Install Simulation — Known Issues and Break Points

Results of a full walkthrough of the setup guide against the actual config files in
this repo, simulating a fresh Ubuntu 24.04 install on identical hardware (HP t630).
Every point of breakage, confusion, or security risk is catalogued below with its
severity and fix. See the summary table at the bottom for a quick reference.

---

## Contents

- [BLOCKERS — will stop a fresh install cold](#blockers--will-stop-a-fresh-install-cold)
  - [1. No `git clone` step in the setup guide](#1-no-git-clone-step-in-the-setup-guide)
  - [2. `wg0.conf` fails to parse — WireGuard will not start](#2-wg0conf-fails-to-parse--wireguard-will-not-start)
- [HIGH — will cause significant confusion or debugging time](#high--will-cause-significant-confusion-or-debugging-time)
  - [3. Host DNS breaks between Steps 3 and 4 and the warning is in the wrong place](#3-host-dns-breaks-between-steps-3-and-4-and-the-warning-is-in-the-wrong-place)
  - [4. `FTLCONF_webserver_api_password: "CHANGE_ME"` — easy to overlook, starts Pi-hole with a known password](#4-ftlconf_webserver_api_password-change_me--easy-to-overlook-starts-pi-hole-with-a-known-password)
- [MEDIUM — silent or hard-to-diagnose failures](#medium--silent-or-hard-to-diagnose-failures)
  - [5. Monitoring script placeholder tokens cause silent `curl` failures](#5-monitoring-script-placeholder-tokens-cause-silent-curl-failures)
  - [6. Crontab `USERNAME` placeholder must be replaced manually](#6-crontab-username-placeholder-must-be-replaced-manually)
  - [7. UFW INPUT rules did not restrict Pi-hole's published port 53 (now fixed by host networking)](#7-ufw-input-rules-did-not-restrict-pi-holes-published-port-53-now-fixed-by-host-networking)
- [MINOR — cosmetic or low-impact](#minor--cosmetic-or-low-impact)
  - [8. `server.conf` indentation inconsistency](#8-serverconf-indentation-inconsistency)
  - [9. `sysctl.conf` append is not idempotent](#9-sysctlconf-append-is-not-idempotent)
  - [10. GRUB edit shows the target string but not a safe append command](#10-grub-edit-shows-the-target-string-but-not-a-safe-append-command)
  - [11. MAC address not mentioned in Step 0](#11-mac-address-not-mentioned-in-step-0)
  - [12. Cache dump correctness depends on Ubuntu's base unbound unit having no `ExecStop`](#12-cache-dump-correctness-depends-on-ubuntus-base-unbound-unit-having-no-execstop)
  - [13. Host-networked Pi-hole vs systemd-resolved on port 53 — now asserted in repo](#13-host-networked-pi-hole-vs-systemd-resolved-on-port-53--now-asserted-in-repo)
- [Consolidation note (2026-06-02)](#consolidation-note-2026-06-02)
- [Replicability pass (2026-06-02)](#replicability-pass-2026-06-02)
  - [14. Pi-hole v5 → v6 environment scheme — compose used variables v6 ignores (BLOCKER)](#14-pi-hole-v5--v6-environment-scheme--compose-used-variables-v6-ignores-blocker)
  - [13 (resolved). Host-net Pi-hole vs systemd-resolved stub — now asserted](#13-resolved-host-net-pi-hole-vs-systemd-resolved-stub--now-asserted)
  - [Live-box verification (2026-06-02)](#live-box-verification-2026-06-02)
- [Summary](#summary)

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

When `docker compose up -d` succeeds and Pi-hole starts, it binds `0.0.0.0:53`
directly on the host (Pi-hole is `network_mode: host`). That collides with the
`:53` that systemd-resolved's stub listener (`127.0.0.53:53`) occupies, and takes
over host-wide DNS. Host DNS breaks immediately. Any diagnostic command you naturally
try next (`docker compose logs`, `apt`, `curl`) fails with "Temporary failure in name
resolution."

Two consequences of host networking to be aware of here: (a) Pi-hole fails to bind
`:53` at all while the stub listener still holds it — it must be disabled with
`DNSStubListener=no` (now asserted, item 13); and (b) once `:53` is taken over, the
host cannot resolve for itself unless its resolution is decoupled onto external
resolvers.

The original SETUP.md warned "Do this immediately after Pi-hole starts" but placed
the warning *after* the `docker compose up -d` command. A first-time installer will
almost certainly try `docker compose logs -f pihole` next, get stuck, and not
understand why.

**Fix (now applied):** README.md reorders the combined block so the host-DNS fix runs
*first* — free `:53` (`DNSStubListener=no`) and re-point `/etc/resolv.conf` off the
stub before `docker compose up -d`. The sequence is: free `:53` + decouple host DNS →
verify `:53` is empty → start Pi-hole. This removes the broken-DNS window entirely
instead of racing to close it.

---

### 4. `FTLCONF_webserver_api_password: "CHANGE_ME"` — easy to overlook, starts Pi-hole with a known password

**Location:** `02-pihole/docker-compose.yml`

The compose file is committed with `FTLCONF_webserver_api_password: "CHANGE_ME"`. If
an installer runs `docker compose up -d` without editing it first, Pi-hole starts
with a publicly-known credential. The old guide flagged it as a note in running
prose — easy to skim past when following step-by-step instructions.

**Fix (now applied):** README.md makes changing the password the first sub-step of
the Pi-hole start step, before the `docker compose up -d` command.

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

**Location:** README.md crontab instructions

```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

Copying this literally into crontab creates a job that runs a path that doesn't exist.
No obvious error — `cron` just logs "command not found" to syslog.

**Fix (now applied):** README.md replaces `USERNAME` with `USER` and adds a reminder
to substitute the actual username.

---

### 7. UFW INPUT rules did not restrict Pi-hole's published port 53 (now fixed by host networking)

**Location:** `04-ufw/setup.sh`, `02-pihole/docker-compose.yml`

**Original problem:** with Pi-hole on the Docker bridge publishing ports, Docker
inserted DNAT rules into the `DOCKER` iptables chain, processed *before* UFW's INPUT
chain. Pi-hole port 53 (published via `ports: "53:53/udp"`) bypassed UFW's
`from 192.168.0.0/16` restriction entirely — UFW's rules only gate host-resident
services, not Docker-published ports. LAN isolation for port 53 relied entirely on
the router.

**Resolved by the consolidation:** Pi-hole now runs `network_mode: host`. Its `:53`
and `:8080` bind directly on the host, so they are subject to UFW's INPUT chain like
any host service — the `from 192.168.0.0/16` and `from 10.8.0.0/24` rules genuinely
restrict them now. Host networking closes the DNAT-bypass gap as a side effect of
the VPN-peer-DNS fix. README.md's UFW note reflects this.

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

### 13. Host-networked Pi-hole vs systemd-resolved on port 53 — now asserted in repo

**Location:** `02-pihole/docker-compose.yml`, `03-host-dns/host-dns.conf`

The consolidated config runs Pi-hole with `network_mode: host` (this is what fixes
VPN-peer DNS). Pi-hole then wants `0.0.0.0:53`, which **collides with
systemd-resolved's stub listener** on `127.0.0.53:53`. On a fresh install Pi-hole
fails to bind `:53` until the stub listener is disabled.

**Fix (now applied):** `03-host-dns/host-dns.conf` now sets `DNSStubListener=no`
alongside `DNS=9.9.9.9 1.1.1.1`. Because disabling the stub removes the
`127.0.0.53` listener that `/etc/resolv.conf` normally points at, README Step 3
also re-points `/etc/resolv.conf` to `/run/systemd/resolve/resolv.conf` (the file
that lists the external resolvers directly), and the install order was changed so
the host-DNS fix runs *before* Pi-hole starts — `:53` is free when FTL launches.

**Live-box caveat:** the live t630 may already free `:53` by a different mechanism
(it has been running host-networked). Before re-applying on the box, check the
current state (`sudo ss -ulpn 'sport = :53'`, `resolvectl status`, `readlink
/etc/resolv.conf`) so you understand what is already in place — see the queued
live-box command list rather than blindly copying the fresh-install steps.

---

## Consolidation note (2026-06-02)

This file and the rest of the repo were consolidated from five divergent branches
into a single source of truth on `main`. The substantive behavioral change adopted
during consolidation: **Pi-hole moved from Docker bridge networking to
`network_mode: host`**, which resolved the project's headline open issue (VPN-peer
DNS over the tunnel) and, as a side effect, brought Pi-hole's ports under UFW's
control (item 7). Items 1, 2, 8, 9, 10, 11 were already fixed in the renovated docs;
items 5, 6, 12 remain operational cautions; item 13 is the one new verify-on-box item
introduced by the host-networking change.

---

## Replicability pass (2026-06-02)

A second walkthrough against current upstream package versions found two more
fresh-install breaks and made item 13 deterministic:

### 14. Pi-hole v5 → v6 environment scheme — compose used variables v6 ignores (BLOCKER)

**Location:** `02-pihole/docker-compose.yml`

`image: pihole/pihole:latest` now pulls **Pi-hole v6**, which replaced the entire v5
environment scheme. The compose file shipped with v5 variables that v6 silently
ignores, so a literal fresh install came up broken in three ways at once:

| v5 variable (ignored by v6) | v6 replacement | Symptom if ignored |
| --- | --- | --- |
| `WEBPASSWORD` | `FTLCONF_webserver_api_password` | Random web password (printed once in logs) |
| `WEB_PORT: "8080"` | `FTLCONF_webserver_port` | **UI binds `:80`, not `:8080`** — UFW only opens 8080, so the admin UI is unreachable on LAN and over WireGuard |
| `PIHOLE_DNS_` | `FTLCONF_dns_upstreams` | Upstream unset → Pi-hole uses its own defaults, **bypassing the entire Unbound streaming/privacy split** |
| `DNSMASQ_USER`, `FTL_CMD` | (removed) | No-ops |
| *(set in UI)* | `FTLCONF_dns_listeningMode: "all"` | "Permit all origins" now seeded/locked, not a manual UI step |

The `WEB_PORT` failure is the nastiest: the UI silently moves to a UFW-blocked port,
so it looks like a firewall problem rather than a config one.

**Fix (now applied):** `02-pihole/docker-compose.yml` migrated to `FTLCONF_*` keys.
The `dnsmasq_data:/etc/dnsmasq.d` mount was dropped (v6 stores dnsmasq config under
`/etc/pihole`), and `cap_add: SYS_NICE` added per the v6 example. Each `FTLCONF_` var
is re-applied and locked on every start, which also largely resolves the "Live
Pi-hole upstreams ≠ repo" caution (item in README known issues): a stale upstream in
an old volume is now overridden on start.

### 13 (resolved). Host-net Pi-hole vs systemd-resolved stub — now asserted

`DNSStubListener=no` added to `03-host-dns/host-dns.conf`; README Steps 3–4 reordered
to free `:53` before Pi-hole starts and to re-point `/etc/resolv.conf` off the stub.
See the updated item 13 above. Live-box reconciliation is now a guided check, not an
unknown.

### Live-box verification (2026-06-02)

Confirmed against the running t630 (SSH `192.168.1.118`):

- **Item 14 reproduced live:** the box was running Pi-hole **v6** (Core v6.4.1 /
  FTL v6.6) with the *old v5-var* compose. FTL had fallen back to the v6 default web
  port, binding `:80`/`:443` instead of `:8080` — and since UFW only opens `:8080`,
  the admin UI was firewalled off on the LAN. Deploying the `FTLCONF_*` compose moved
  the UI back to `:8080` (`curl …:8080/admin/` → `302`). This is the clearest
  real-world proof of the v5→v6 break.
- **Stub location:** on the live box `DNSStubListener=no` is set in the **main**
  `/etc/systemd/resolved.conf` (not the drop-in), and `/etc/resolv.conf` already
  points at `/run/systemd/resolve/resolv.conf`. The repo asserts the same via the
  version-controlled drop-in `03-host-dns/host-dns.conf`, which is additive (a
  redundant `DNSStubListener=no` is harmless) and is the cleaner reproducible pattern.
- **WireGuard peers reconciled:** `wg show` listed six peers (`10.8.0.2`–`.7`). Their
  real public keys are now in `05-wireguard/wg0.conf`. `.2` (iPhone) and `.3` (Windows
  laptop) are active; `.4`/`.5`/`.6` have no handshake and remain UNIDENTIFIED; `.7`
  is the Mac. The laptop key rotation is still outstanding.

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
| 7 | Resolved | `04-ufw/setup.sh`, `02-pihole/` | UFW port-53 bypass — closed by moving Pi-hole to host networking |
| 8 | Minor | `01-unbound/server.conf` | Indentation inconsistency on `interface:` line |
| 9 | Minor | README.md Step 6 | `sysctl.conf` append not idempotent |
| 10 | Minor | README.md Step 9 | GRUB edit guidance incomplete — risk of clobbering existing flags |
| 11 | Minor | README.md Step 0 | No guidance on finding the MAC address |
| 12 | Minor | `unbound.service.d/override.conf` | Cache dump assumes base unit has no `ExecStop` |
| 13 | Resolved in repo | `02-pihole/`, `03-host-dns/` | Host-net Pi-hole vs systemd-resolved stub on `:53` — `DNSStubListener=no` now asserted + resolv.conf re-point |
| 14 | **BLOCKER** | `02-pihole/docker-compose.yml` | Pi-hole v6 ignores the v5 env vars (`WEBPASSWORD`, `WEB_PORT`, `PIHOLE_DNS_`) — UI on wrong port, upstream unset; migrated to `FTLCONF_*` |
