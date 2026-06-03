# Fresh Install Simulation — Known Issues and Break Points

Results of a full walkthrough of the setup guide against the actual config files in
this repo, simulating a fresh Ubuntu 24.04 install on identical hardware (HP t630).
Every point of breakage, confusion, or security risk is catalogued below with its
severity and fix. Items are numbered and ordered by where they surface during a
fresh install (README Steps 0–11). Original discovery numbers are cross-referenced
in the Summary Table. Ongoing operational issues — moved here from the README's
old "Known issues" table, and *not* fresh-install break points — are collected
under [Operational & Open Issues](#operational--open-issues).

Every `Location:` path links to the file in this repo, so a resolved-in-repo fix
is one click away.

---

## Contents

**Fresh-install break points** (in install order)

**Pre-install**
- [1. No `git clone` step in the setup guide](#1-no-git-clone-step-in-the-setup-guide) `BLOCKER` — **--RESOLVED 2026-06-02--**

**Step 0 — Router DHCP Reservation**
- [2. MAC address not mentioned in Step 0](#2-mac-address-not-mentioned-in-step-0) `MINOR` — **--RESOLVED 2026-06-02--**

**Step 2 — Unbound**
- [3. `server.conf` indentation inconsistency](#3-serverconf-indentation-inconsistency) `MINOR` — **--RESOLVED 2026-06-02--**
- [4. Cache dump correctness depends on Ubuntu's base unbound unit having no `ExecStop`](#4-cache-dump-correctness-depends-on-ubuntus-base-unbound-unit-having-no-execstop) `MINOR` `ONGOING CAUTION`

**Steps 4+5 — Host DNS Fix, then Pi-hole**
- [5. Host DNS breaks between Steps 4 and 5, warning in the wrong place](#5-host-dns-breaks-between-steps-4-and-5-warning-in-the-wrong-place) `HIGH` — **--RESOLVED 2026-06-02--**
- [6. `FTLCONF_webserver_api_password: "CHANGE_ME"` — easy to overlook](#6-ftlconf_webserver_api_password-change_me--easy-to-overlook) `HIGH` `SECURITY` — **--RESOLVED 2026-06-02--**
- [7. Pi-hole v5→v6 environment scheme — compose used variables v6 ignores](#7-pi-hole-v5v6-environment-scheme--compose-used-variables-v6-ignores) `BLOCKER` — **--RESOLVED 2026-06-02--**
- [8. UFW INPUT rules did not restrict Pi-hole's published port 53](#8-ufw-input-rules-did-not-restrict-pi-holes-published-port-53) `MEDIUM` — **--RESOLVED 2026-06-02--**
- [9. Host-networked Pi-hole vs systemd-resolved stub on port 53](#9-host-networked-pi-hole-vs-systemd-resolved-stub-on-port-53) `MEDIUM` — **--RESOLVED 2026-06-02--**

**Step 7 — VPN (WireGuard)**
- [10. `wg0.conf` fails to parse — WireGuard will not start](#10-wg0conf-fails-to-parse--wireguard-will-not-start) `BLOCKER` — **--RESOLVED 2026-06-02--**
- [11. `sysctl.conf` append is not idempotent](#11-sysctlconf-append-is-not-idempotent) `MINOR` — **--RESOLVED 2026-06-02--**

**Step 8 — Uptime Kuma**
- [12. Monitoring script placeholder tokens cause silent `curl` failures](#12-monitoring-script-placeholder-tokens-cause-silent-curl-failures) `MEDIUM` `OPERATIONAL CAUTION`
- [13. Crontab `USERNAME` placeholder must be replaced manually](#13-crontab-username-placeholder-must-be-replaced-manually) `MEDIUM` `OPERATIONAL CAUTION`

**Step 9 — GPU Performance**
- [14. GRUB edit shows the target string but not a safe append command](#14-grub-edit-shows-the-target-string-but-not-a-safe-append-command) `MINOR` — **--RESOLVED 2026-06-02--**

**Other**
- [Operational & Open Issues](#operational--open-issues) (moved from README)
- [Audit Log](#audit-log)
- [Summary Table](#summary-table)

---

## Pre-install

---

### 1. No `git clone` step in the setup guide

`BLOCKER` | `docs` | **Location:** [`README.md`](README.md), top of Setup section

> ✓ **RESOLVED — 2026-06-02**

**Problem**

Every `cp` command in the setup guide uses relative paths (`01-unbound/*.conf`,
`06-cake/setup.sh`, etc.). Without first cloning the repo to the t630 and
`cd`-ing into it, every single one of those commands fails with
"No such file or directory" — before a single service is configured.

**Fix**

[`README.md`](README.md) now opens the Setup section with an explicit
clone-and-cd step:

```bash
git clone https://github.com/a777ance/localdns ~/localdns
cd ~/localdns
```

---

## Step 0 — Router DHCP Reservation

---

### 2. MAC address not mentioned in Step 0

`MINOR` | `docs` | **Location:** [`README.md`](README.md), Step 0

> ✓ **RESOLVED — 2026-06-02**

**Problem**

DHCP reservation requires the t630's MAC address. On a fresh install the MAC is
on a label on the device or in the router's current lease table — but a
first-time installer may not know how to find it in the OS.

**Fix**

[`README.md`](README.md) now adds `ip link show enp1s0` (read the `link/ether`
value) as the first sub-step of Step 0.

---

## Step 2 — Unbound

---

### 3. `server.conf` indentation inconsistency

`MINOR` | `config` | **Location:** [`01-unbound/server.conf`](01-unbound/server.conf), line 6

> ✓ **RESOLVED — 2026-06-02**

**Problem**

The `interface:` line has 6 spaces of indentation while all other lines have 4.
Unbound's parser is whitespace-insensitive so this is harmless, but it looks wrong.

**Fix**

Corrected to 4 spaces.

---

### 4. Cache dump correctness depends on Ubuntu's base unbound unit having no `ExecStop`

`MINOR` | `systemd` | **Location:** [`01-unbound/unbound.service.d/override.conf`](01-unbound/unbound.service.d/override.conf)

> ⚠ **ONGOING CAUTION — Monitor on Ubuntu package upgrades**

**Problem**

[`override.conf`](01-unbound/unbound.service.d/override.conf) adds
`ExecStop=/usr/local/bin/unbound-cache-dump`. Systemd runs `ExecStop` commands
before sending SIGTERM to the main process, so `unbound-control dump_cache` can
still talk to a running Unbound. This is correct — *provided* the base
`unbound.service` unit on Ubuntu has no explicit `ExecStop` of its own. On
Ubuntu 24.04 LTS, the base unit uses SIGTERM with no `ExecStop`: the assumption
holds.

A future distro update adding `ExecStop=/usr/sbin/unbound-control stop` to the
base unit would silently break cache dumps on every shutdown — the base
`ExecStop` would fire first, shut Unbound down, and the dump script would then
fail to connect.

**Mitigation**

Monitor Ubuntu's `unbound` package changelogs when upgrading. If the base unit
ever gains an explicit stop command, migrate the dump to `ExecStopPost` or reset
the `ExecStop=` list in the override before redefining it.

---

## Steps 4+5 — Host DNS Fix, then Pi-hole

---

### 5. Host DNS breaks between Steps 4 and 5, warning in the wrong place

`HIGH` | `pihole` `networking` | **Location:** [`README.md`](README.md), Steps 4–5

> ✓ **RESOLVED — 2026-06-02**

**Problem**

When `docker compose up -d` succeeds and Pi-hole starts, it binds `0.0.0.0:53`
directly on the host (`network_mode: host`), colliding with systemd-resolved's
stub listener on `127.0.0.53:53` and taking over host-wide DNS. Any diagnostic
command tried next (`docker compose logs`, `apt`, `curl`) fails with
"Temporary failure in name resolution."

Two consequences of host networking: (a) Pi-hole fails to bind `:53` at all
while the stub listener still holds it; and (b) once `:53` is taken over, the
host cannot resolve for itself unless its resolution is decoupled onto external
resolvers.

The original guide warned "Do this immediately after Pi-hole starts" but placed
the warning *after* the `docker compose up -d` command — a first-time installer
hits the broken-DNS window before seeing it.

**Fix**

[`README.md`](README.md) reorders the block so the host-DNS fix runs *first*:
free `:53` (`DNSStubListener=no`) and re-point `/etc/resolv.conf` off the stub
*before* `docker compose up -d`. Sequence: free `:53` + decouple host DNS →
verify `:53` is empty → start Pi-hole. This eliminates the broken-DNS window
entirely.

---

### 6. `FTLCONF_webserver_api_password: "CHANGE_ME"` — easy to overlook

`HIGH` | `security` `pihole` | **Location:** [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

The compose file is committed with `FTLCONF_webserver_api_password: "CHANGE_ME"`.
If an installer runs `docker compose up -d` without editing it first, Pi-hole
starts with a publicly-known credential. The old guide flagged it as a note in
running prose — easy to skim past when following step-by-step instructions.

**Fix**

[`README.md`](README.md) makes changing the password the explicit first sub-step
of the Pi-hole start block, before the `docker compose up -d` command. (The
placeholder itself remains an operational must-do on each fresh deploy — see
[Operational & Open Issues](#operational--open-issues).)

---

### 7. Pi-hole v5→v6 environment scheme — compose used variables v6 ignores

`BLOCKER` | `pihole` `docker` | **Location:** [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

`image: pihole/pihole:latest` now pulls Pi-hole v6, which replaced the entire v5
environment scheme. The compose file shipped with v5 variables that v6 silently
ignores:

| v5 variable (ignored by v6) | v6 replacement | Symptom if ignored |
| --- | --- | --- |
| `WEBPASSWORD` | `FTLCONF_webserver_api_password` | Random web password (printed once in logs) |
| `WEB_PORT: "8080"` | `FTLCONF_webserver_port` | **UI binds `:80`, not `:8080`** — UFW only opens 8080; admin UI unreachable on LAN and over WireGuard |
| `PIHOLE_DNS_` | `FTLCONF_dns_upstreams` | Upstream unset → Pi-hole uses defaults, **bypassing the entire Unbound streaming/privacy split** |
| `DNSMASQ_USER`, `FTL_CMD` | (removed) | No-ops |
| *(set manually in UI)* | `FTLCONF_dns_listeningMode: "all"` | "Permit all origins" now seeded/locked via env |

The `WEB_PORT` failure is the nastiest: the UI silently moves to a UFW-blocked
port, so it presents as a firewall problem rather than a config one.
**Confirmed live:** the box was running Pi-hole v6 (Core v6.4.1 / FTL v6.6)
with the old v5-var compose — FTL fell back to the v6 default web port, binding
`:80`/`:443` instead of `:8080`, and the admin UI was firewalled off on the LAN.

**Fix**

[`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) migrated to
`FTLCONF_*` keys. The `dnsmasq_data:/etc/dnsmasq.d` mount was dropped (v6 stores
dnsmasq config under `/etc/pihole`), and `cap_add: SYS_NICE` added per the v6
example. Each `FTLCONF_` var is re-applied and locked on every start, which also
resolves the "Live Pi-hole upstreams ≠ repo" caution: a stale upstream in an old
volume is now overridden on start.

---

### 8. UFW INPUT rules did not restrict Pi-hole's published port 53

`MEDIUM` | `ufw` `docker` `security` | **Location:** [`04-ufw/setup.sh`](04-ufw/setup.sh), [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

With Pi-hole on the Docker bridge publishing ports, Docker inserted DNAT rules
into the `DOCKER` iptables chain, processed *before* UFW's INPUT chain.
Pi-hole port 53 (published via `ports: "53:53/udp"`) bypassed UFW's
`from 192.168.0.0/16` restriction entirely — LAN isolation for port 53 relied
entirely on the router's NAT.

**Fix**

Pi-hole now runs `network_mode: host` in
[`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml). Its `:53` and
`:8080` bind directly on the host and are subject to UFW's INPUT chain
([`04-ufw/setup.sh`](04-ufw/setup.sh)) like any host service — the
`from 192.168.0.0/16` and `from 10.8.0.0/24` rules genuinely restrict them.
Host networking closes the DNAT-bypass gap as a side effect of the
VPN-peer-DNS fix.

---

### 9. Host-networked Pi-hole vs systemd-resolved stub on port 53

`MEDIUM` | `pihole` `systemd` `networking` | **Location:** [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml), [`03-host-dns/host-dns.conf`](03-host-dns/host-dns.conf)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

Running Pi-hole with `network_mode: host` makes it want `0.0.0.0:53`, which
**collides with systemd-resolved's stub listener** on `127.0.0.53:53`. On a
fresh install Pi-hole fails to bind `:53` until the stub listener is disabled.

**Live-box caveat:** the live t630 may already free `:53` by a different
mechanism. Before re-applying on the box, check current state
(`sudo ss -ulpn 'sport = :53'`, `resolvectl status`, `readlink /etc/resolv.conf`)
— do not blindly copy the fresh-install steps.

**Fix**

[`03-host-dns/host-dns.conf`](03-host-dns/host-dns.conf) now sets
`DNSStubListener=no` alongside `DNS=9.9.9.9 1.1.1.1`. Because disabling the stub
removes the `127.0.0.53` listener that `/etc/resolv.conf` normally points at,
[`README.md`](README.md) Step 4 also re-points `/etc/resolv.conf` to
`/run/systemd/resolve/resolv.conf` (the file that lists the external resolvers
directly). The install order was changed so the host-DNS fix runs *before*
Pi-hole starts — `:53` is free when FTL launches.

---

## Step 7 — VPN (WireGuard)

---

### 10. `wg0.conf` fails to parse — WireGuard will not start

`BLOCKER` | `wireguard` `config` | **Location:** [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

Two problems in the repo file caused `wg-quick@wg0.service` to fail at parse time:

**Problem A — empty `[Peer]` block (Mac peer):**

```
[Peer]
# Mac peer — added via WireGuard macOS (App Store, NOT Homebrew)
# PublicKey = REPLACE_WITH_MAC_PUBLIC_KEY
# AllowedIPs = 10.8.0.7/32
```

The `[Peer]` section header was uncommented but both required fields were
commented out. `wg-quick` encountering a `[Peer]` block with no `PublicKey`
errors out: "A peer is missing a public key."

**Problem B — invalid placeholder key (laptop peer):**

```
PublicKey = REPLACE_WITH_LAPTOP_PUBLIC_KEY
```

`REPLACE_WITH_LAPTOP_PUBLIC_KEY` is not valid base64. `wg` fails with an
invalid key decode error.

The setup instructions only told you to replace the server private key and the
phone public key — they said nothing about fixing the Mac and laptop peer blocks.
An installer following the guide literally would hit `wg-quick@wg0.service`
failing with no obvious reason.

**Fix**

In [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf), the Mac `[Peer]` header is
now commented out alongside its body, and the laptop `PublicKey` line is
commented out with an explicit warning. [`README.md`](README.md) now has an
explicit "fix the peer blocks before deploying" instruction.

---

### 11. `sysctl.conf` append is not idempotent

`MINOR` | `wireguard` `sysctl` | **Location:** [`README.md`](README.md), Step 7 (IP forwarding)

> ✓ **RESOLVED — 2026-06-02**

**Problem**

The original command:
```bash
sudo bash -c 'echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf'
```

Appends to `/etc/sysctl.conf` every time it runs. Running the step twice creates
duplicate lines. Functionally harmless (last value wins) but bad practice.

**Fix**

[`README.md`](README.md) now uses a dedicated drop-in file:
```bash
printf 'net.ipv4.ip_forward=1\nnet.ipv6.conf.all.forwarding=1\n' \
  | sudo tee /etc/sysctl.d/99-wireguard-forward.conf
sudo sysctl --system
```

This is idempotent and follows the proper `sysctl.d` pattern for Ubuntu.

---

## Step 8 — Uptime Kuma

---

### 12. Monitoring script placeholder tokens cause silent `curl` failures

`MEDIUM` | `uptime-kuma` `monitoring` | **Location:** [`07-uptime-kuma/packet-loss-monitor.sh`](07-uptime-kuma/packet-loss-monitor.sh), [`07-uptime-kuma/cake-monitor.sh`](07-uptime-kuma/cake-monitor.sh)

> ⚠ **OPERATIONAL CAUTION — Replace tokens and test manually before scheduling**

**Problem**

Both scripts ship with placeholder push tokens:
- `<PUSH_TOKEN_ROUTER>`, `<PUSH_TOKEN_INTERNET>` in [`packet-loss-monitor.sh`](07-uptime-kuma/packet-loss-monitor.sh)
- `<PUSH_TOKEN_CAKE>` in [`cake-monitor.sh`](07-uptime-kuma/cake-monitor.sh)

`curl` requests to URLs containing literal `<>` fail. All output is redirected to
`/dev/null`, so there is no visible error. The cron jobs fire every minute
indefinitely and the Uptime Kuma monitors never go green. Nothing in the system
logs tells you why.

**Fix**

[`README.md`](README.md) adds an explicit manual test step — run each script once
by hand and confirm the Uptime Kuma monitor flips green *before* adding it to
crontab. Push tokens are per-install values from the Uptime Kuma UI and cannot be
pre-filled in the repo.

---

### 13. Crontab `USERNAME` placeholder must be replaced manually

`MEDIUM` | `uptime-kuma` `cron` | **Location:** [`README.md`](README.md), Step 8 crontab instructions

> ⚠ **OPERATIONAL CAUTION — Substitute real username before adding to crontab**

**Problem**

```
* * * * * /home/USERNAME/packet-loss-monitor.sh
```

Copying this literally into crontab creates a job that runs a path that doesn't
exist. No obvious error — `cron` just logs "command not found" to syslog.

**Fix**

[`README.md`](README.md) replaces `USERNAME` with `USER` and adds a reminder to
substitute the actual username before adding to crontab.

---

## Step 9 — GPU Performance

---

### 14. GRUB edit shows the target string but not a safe append command

`MINOR` | `grub` `gpu` | **Location:** [`README.md`](README.md), Step 9

> ✓ **RESOLVED — 2026-06-02**

**Problem**

Showing the desired final value of `GRUB_CMDLINE_LINUX_DEFAULT` without showing
how to get there safely invites someone to copy the line verbatim and overwrite
existing kernel flags (`quiet splash`, or custom power management parameters
they may have already set).

**Fix**

[`README.md`](README.md) now shows an explicit "append to whatever is already
there" instruction with a before/after example.

---

## Operational & Open Issues

Ongoing operational issues of the live system — **moved here from the README's
old "Known issues" table.** These are distinct from the fresh-install break
points above: some are still open (laptop key, unidentified peers), some are
intentional design constraints (IPv6 black hole), and some are resolved in repo
(linked to the committed file that resolves them). The README now links to this
section by category.

| Issue | Status | Action / Notes | Resolved in repo |
| ----- | ------ | -------------- | ---------------- |
| `FTLCONF_webserver_api_password` placeholder | **Open** | Placeholder (`CHANGE_ME`) — must be changed before the first `docker compose up`. Detailed as Break Point [#6](#6-ftlconf_webserver_api_password-change_me--easy-to-overlook). | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) |
| Windows laptop WireGuard key | **Open** | Private key was exposed during setup; rotate before trusting this peer. | [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf) |
| WireGuard peers `10.8.0.4`–`10.8.0.6` | **Open** — reconciled, still unidentified | Now in the config with their real public keys, but none has a recent handshake — identify each device or remove the stale peer. | [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf) |
| WireGuard `::/0` IPv6 black hole | **Documented** (design constraint) | Server is IPv4-only in-tunnel; do **not** add `::/0` to peer AllowedIPs. IPv6 traffic black-holes silently (handshake succeeds, pages hang). Use `0.0.0.0/0` only. Leak-free dual-stack fix (ULA + NAT66) in [network-context.md](network-context.md). | [`05-wireguard/peer-template.conf`](05-wireguard/peer-template.conf) |
| VPN peer DNS over the tunnel | ✓ **Resolved in repo** | Fixed by Pi-hole `network_mode: host`: the Docker bridge + published-ports DNAT path silently dropped replies to queries sourced from the host's own `wg0` interface; host networking removes the DNAT path so `10.8.0.1:53` answers directly. Port 8080 was also opened to the WG subnet so the Pi-hole UI is reachable over the tunnel. | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) · [`04-ufw/setup.sh`](04-ufw/setup.sh) |
| Live Pi-hole upstreams ≠ repo | ✓ **Mostly resolved** (v6) | Under Pi-hole v6, `FTLCONF_dns_upstreams` is re-applied and locked on every start, overriding any legacy resolvers (`8.8.8.8`, Quad9, etc.) left in the `pihole_data` volume. Still worth confirming the UI shows only `127.0.0.1#5335` after a deploy onto an old volume. | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) |
| Host-net Pi-hole vs systemd-resolved on `:53` | ✓ **Resolved in repo** | `network_mode: host` makes Pi-hole bind `0.0.0.0:53`, colliding with the stub listener (`127.0.0.53:53`). `DNSStubListener=no` frees `:53` and the host-DNS step re-points `/etc/resolv.conf` off the stub. Full detail: Break Point [#9](#9-host-networked-pi-hole-vs-systemd-resolved-stub-on-port-53). | [`03-host-dns/host-dns.conf`](03-host-dns/host-dns.conf) · [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) |
| Pi-hole v5 → v6 env vars | ✓ **Resolved in repo** | `pihole/pihole:latest` is v6, which ignores the v5 env vars (`WEBPASSWORD`, `WEB_PORT`, `PIHOLE_DNS_`, …). Compose migrated to `FTLCONF_*` keys. Full detail: Break Point [#7](#7-pi-hole-v5v6-environment-scheme--compose-used-variables-v6-ignores). | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) |

---

## Audit Log

### Consolidation (2026-06-02)

This file and the rest of the repo were consolidated from five divergent branches
into a single source of truth on `main`. The substantive behavioral change:
**Pi-hole moved from Docker bridge networking to `network_mode: host`**, which
resolved the project's headline open issue (VPN-peer DNS over the tunnel) and,
as a side effect, brought Pi-hole's ports under UFW's control (issue 8 above).
Issues 1, 2, 3, 11, 14 (originally #1, #11, #8, #9, #10) were already fixed in
the renovated docs; issues 12 and 13 remain operational cautions; issue 9
(originally #13) is the one new verify-on-box item introduced by the
host-networking change.

### Replicability Pass (2026-06-02)

A second walkthrough against current upstream package versions found two more
fresh-install breaks and made issue 9 deterministic:

- **Issue 7 (originally #14)** discovered and fixed: Pi-hole v6 ignores v5 env
  vars. [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) migrated
  to `FTLCONF_*`. Confirmed live: the box was running Pi-hole v6 (Core v6.4.1 /
  FTL v6.6) with the old v5-var compose — FTL had fallen back to `:80`/`:443`,
  and since UFW only opens `:8080`, the admin UI was firewalled off on the LAN.
  Deploying the `FTLCONF_*` compose moved the UI back to `:8080`
  (`curl …:8080/admin/` → `302`).
- **Issue 9 (originally #13)** made deterministic: `DNSStubListener=no` confirmed
  correct in both the repo drop-in
  ([`03-host-dns/host-dns.conf`](03-host-dns/host-dns.conf)) and (independently)
  the live box. The drop-in is additive — a redundant `DNSStubListener=no` is
  harmless.
- **WireGuard peers reconciled:** `wg show` listed six peers (`10.8.0.2`–`.7`).
  Real public keys now in [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf). `.2`
  (iPhone) and `.3` (Windows laptop) active; `.4`/`.5`/`.6` have no handshake
  and remain UNIDENTIFIED; `.7` is the Mac. Laptop key rotation still
  outstanding.

---

## Summary Table

Items numbered in README install order. "Orig #" is the original discovery number
from the first simulation walkthrough. Ongoing operational items are tracked
separately under [Operational & Open Issues](#operational--open-issues).

| # | Orig # | Severity | README Step | Location | Impact | Status |
|---|--------|----------|-------------|----------|--------|--------|
| 1 | #1 | **BLOCKER** | Pre-install | [`README.md`](README.md) | No `git clone` — all `cp` commands fail immediately | ✓ RESOLVED 2026-06-02 |
| 2 | #11 | Minor | Step 0 | [`README.md`](README.md) | No guidance on finding the MAC address | ✓ RESOLVED 2026-06-02 |
| 3 | #8 | Minor | Step 2 | [`01-unbound/server.conf`](01-unbound/server.conf) | Indentation inconsistency on `interface:` line | ✓ RESOLVED 2026-06-02 |
| 4 | #12 | Minor | Step 2 | [`unbound.service.d/override.conf`](01-unbound/unbound.service.d/override.conf) | Cache dump assumes base unit has no `ExecStop` | ⚠ ONGOING CAUTION |
| 5 | #3 | High | Steps 4+5 | [`README.md`](README.md) | Host DNS breaks silently; warning was in the wrong place | ✓ RESOLVED 2026-06-02 |
| 6 | #4 | High | Steps 4+5 | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) | Known-weak default password easy to miss | ✓ RESOLVED 2026-06-02 |
| 7 | #14 | **BLOCKER** | Steps 4+5 | [`02-pihole/docker-compose.yml`](02-pihole/docker-compose.yml) | Pi-hole v6 ignores v5 env vars — UI on wrong port, upstream unset | ✓ RESOLVED 2026-06-02 |
| 8 | #7 | Medium | Steps 4+5 | [`04-ufw/setup.sh`](04-ufw/setup.sh), [`02-pihole/`](02-pihole/docker-compose.yml) | UFW port-53 bypass — closed by host networking | ✓ RESOLVED 2026-06-02 |
| 9 | #13 | Medium | Steps 4+5 | [`02-pihole/`](02-pihole/docker-compose.yml), [`03-host-dns/`](03-host-dns/host-dns.conf) | Host-net Pi-hole vs systemd-resolved stub — `DNSStubListener=no` now asserted | ✓ RESOLVED 2026-06-02 |
| 10 | #2 | **BLOCKER** | Step 7 | [`05-wireguard/wg0.conf`](05-wireguard/wg0.conf) | Malformed peer blocks — `wg-quick@wg0` fails to parse | ✓ RESOLVED 2026-06-02 |
| 11 | #9 | Minor | Step 7 | [`README.md`](README.md) | `sysctl.conf` append not idempotent | ✓ RESOLVED 2026-06-02 |
| 12 | #5 | Medium | Step 8 | [`07-uptime-kuma/*.sh`](07-uptime-kuma/packet-loss-monitor.sh) | Silent `curl` failures when push tokens not replaced | ⚠ OPERATIONAL CAUTION |
| 13 | #6 | Medium | Step 8 | [`README.md`](README.md) | `USERNAME` crontab placeholder creates broken cron job | ⚠ OPERATIONAL CAUTION |
| 14 | #10 | Minor | Step 9 | [`README.md`](README.md) | GRUB edit guidance incomplete — risk of clobbering existing flags | ✓ RESOLVED 2026-06-02 |
