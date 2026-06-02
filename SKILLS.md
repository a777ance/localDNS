# Skills demonstrated

This document maps the engineering skills exercised in building and operating
this stack to the concrete artifacts in the repo. Every technical claim below
points at the file(s) that prove it — nothing here is aspirational.

It is the long-form companion to the condensed skills summary on the resume:
the resume name-drops, this explains.

---

## Networking, VPN & Security

- **WireGuard VPN** — self-hosted server; multi-peer (iOS / macOS / Windows);
  key-pair lifecycle and rotation; full-tunnel routing with NAT masquerade;
  `PersistentKeepalive`; MTU tuning for cellular; IPv6 split-tunnel
  troubleshooting (handshake-OK / black-hole diagnosis).
  → `wireguard/wg0.conf`, `wireguard/peer-template.conf`,
  `network-context.md` (WireGuard runbooks)
- **DNS privacy** — DNSSEC validation; DNS-over-TLS encrypted upstreams to
  Cloudflare (`1.1.1.1@853`, cert-validated); split-horizon forwarding so
  sensitive lookups stay recursive and private.
  → `unbound/streaming-forward.conf`, `unbound/root-auto-trust-anchor-file.conf`,
  `unbound/server.conf`
- **Network-wide DNS filtering** — Pi-hole at the edge, single-upstream design
  feeding Unbound.
  → `pihole/docker-compose.yml`
- **Firewall** — UFW / iptables; default-deny incoming; per-subnet scoping
  (RFC1918 + WireGuard `10.8.0.0/24`); single WAN-exposed port; NAT; DSCP
  packet marking via the `mangle` table.
  → `ufw/setup.sh`, `cake/setup.sh`
- **QoS / traffic shaping** — CAKE SQM for bufferbloat remediation; `diffserv4`
  prioritization; DNS responses marked DSCP EF into the highest-priority tin.
  Cut loaded latency from ~800 ms to ~15 ms.
  → `cake/setup.sh`, `systemd/cake.service`
- **Network diagnostics** — `dig`, `tcpdump`, `mtr`, three-hop fault isolation,
  packet-loss analysis.
  → `scripts/packet-loss-monitor.sh`, `network-context.md` (diagnostics)

---

## Systems & Infrastructure

- **Linux administration** — Ubuntu / Debian; headless server operation.
- **systemd** — authoring services, timers, and `service.d` drop-in overrides;
  hooking scripts into unit lifecycle.
  → `systemd/` (services, timers, `unbound.service.d/override.conf`)
- **udev rules** — re-asserting hardware state on device events.
  → `udev/99-amdgpu-performance.rules`
- **Unbound recursive resolver** — cache sizing/slabs, TTL policy, prefetch,
  serve-expired; cache persistence across reboots.
  → `unbound/tuning.conf`, `scripts/unbound-cache-dump`,
  `scripts/unbound-cache-load`, `systemd/unbound-cache-dump.timer`
- **Docker / Docker Compose** — bridge vs. host networking, container-to-host
  networking (`172.17.0.1` bridge gateway), named volumes vs. bind mounts.
  → `pihole/docker-compose.yml`, `uptime-kuma/docker-compose.yml`
- **Monitoring** — Uptime Kuma multi-layer health checks (DNS / TCP / HTTP /
  push heartbeats) isolating failures to a single component.
  → `uptime-kuma/docker-compose.yml`, `scripts/cake-monitor.sh`,
  `scripts/packet-loss-monitor.sh`
- **Hardware / performance tuning** — headless thin-client (HP t630) deployment;
  CPU governor and AMD GPU forced to performance mode against headless
  downclocking.
  → `systemd/cpu-performance.service`, `systemd/gpu-performance.service`,
  `udev/99-amdgpu-performance.rules`
- **Remote access** — SSH, xrdp, NoMachine; reachable over the WireGuard subnet.
  → `nomachine/server.cfg`, `ufw/setup.sh`

---

## Automation, Scripting & Tooling

- **Bash** — idempotent provisioning and monitoring scripts (`set -euo
  pipefail`, delete-before-add idempotency, PCRE parsing, curl push reporting).
  → `cake/setup.sh`, `ufw/setup.sh`, `scripts/*`
- **Scheduling** — cron-driven monitors feeding a push-based dashboard.
  → `scripts/packet-loss-monitor.sh`, `scripts/cake-monitor.sh`
- **Python**, **SQL**
- **Git / GitHub** — feature-branch and pull-request workflow (visible
  throughout this repo's history).
- **VS Code**
- **REST API integration**; **Claude API integration** for compliance workflows
- **Infrastructure-as-config** — the entire repo is a version-controlled config
  snapshot and rollback target; every file maps to a documented deploy path.
  → `CLAUDE.md`, `SETUP.md`

---

## Professional background (beyond this repo)

Domain skills from prior work, not exercised by this project but part of the
broader toolkit:

PensionPro; Salesforce (custom dashboards, validated reports, workflow
automation); advanced Microsoft Excel (XLOOKUP, macros, pivot tables); ESOP
administration software; TValue 6 (amortization); Microsoft Access; SharePoint;
Microsoft Office Suite.
