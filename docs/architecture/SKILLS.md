# Skills demonstrated

This document maps the engineering skills exercised in building and operating
this stack to the concrete artifacts in the repo. Every technical claim below
points at the file(s) that prove it — nothing here is aspirational.

It is the long-form companion to the condensed skills summary on the resume:
the resume name-drops, this explains.

---

## Contents

- [0. Networking, VPN & Security](#0-networking-vpn--security)
- [A. Systems & Infrastructure](#a-systems--infrastructure)
- [B. Automation, Scripting & Tooling](#b-automation-scripting--tooling)
- [1. Professional background (beyond this repo)](#1-professional-background-beyond-this-repo)

---

## 0. Networking, VPN & Security

- **WireGuard VPN** — self-hosted server; multi-peer (iOS / macOS / Windows);
  key-pair lifecycle and rotation; full-tunnel routing with NAT masquerade;
  `PersistentKeepalive`; MTU tuning for cellular; IPv6 split-tunnel
  troubleshooting (handshake-OK / black-hole diagnosis).
  → `01-core-network/wireguard/wg0.conf`, `01-core-network/wireguard/peer-template.conf`,
  `network-context.md` (WireGuard runbooks)
- **DNS privacy** — DNSSEC validation; DNS-over-TLS encrypted upstreams to
  Cloudflare (`1.1.1.1@853`, cert-validated); split-horizon forwarding so
  sensitive lookups stay recursive and private.
  → `01-core-network/unbound/streaming-forward.conf`, `01-core-network/unbound/root-auto-trust-anchor-file.conf`,
  `01-core-network/unbound/server.conf`
- **Network-wide DNS filtering** — Pi-hole at the edge, single-upstream design
  feeding Unbound; host-networked so it answers VPN peers over `wg0`.
  → `01-core-network/pihole/docker-compose.yml`
- **Firewall** — UFW / iptables; default-deny incoming; per-subnet scoping
  (RFC1918 + WireGuard `10.8.0.0/24`); single WAN-exposed port; NAT; DSCP
  packet marking via the `mangle` table.
  → `01-core-network/ufw/setup.sh`, `02-performance/cake/setup.sh`
- **QoS / traffic shaping** — CAKE SQM for bufferbloat remediation; `diffserv4`
  prioritization; DNS responses marked DSCP EF into the highest-priority tin.
  Cut loaded latency from ~800 ms to ~15 ms.
  → `02-performance/cake/setup.sh`, `02-performance/cake/cake.service`
- **Network diagnostics** — `dig`, `tcpdump`, `mtr`, three-hop fault isolation,
  packet-loss analysis.
  → `03-monitoring/monitors/packet-loss-monitor.sh`, `network-context.md` (diagnostics)

---

## A. Systems & Infrastructure

- **Linux administration** — Ubuntu / Debian; headless server operation.
- **systemd** — authoring services, timers, and `service.d` drop-in overrides;
  hooking scripts into unit lifecycle.
  → `01-core-network/unbound/unbound-cache-dump.service`, `01-core-network/unbound/unbound-cache-dump.timer`,
  `01-core-network/unbound/unbound.service.d/override.conf`, `02-performance/cake/cake.service`,
  `02-performance/gpu-performance/*.service`
- **udev rules** — re-asserting hardware state on device events.
  → `02-performance/gpu-performance/99-amdgpu-performance.rules`
- **Unbound recursive resolver** — cache sizing/slabs, TTL policy, prefetch,
  serve-expired; cache persistence across reboots.
  → `01-core-network/unbound/tuning.conf`, `01-core-network/unbound/unbound-cache-dump`,
  `01-core-network/unbound/unbound-cache-load`, `01-core-network/unbound/unbound-cache-dump.timer`
- **Docker / Docker Compose** — bridge vs. host networking and when each is
  correct (the bridge-gateway `172.17.0.1` DNAT path silently dropped VPN-peer
  DNS, which drove the move to `network_mode: host`); named volumes vs. bind mounts.
  → `01-core-network/pihole/docker-compose.yml`, `03-monitoring/uptime-kuma/docker-compose.yml`
- **Monitoring** — Uptime Kuma multi-layer health checks (DNS / TCP / HTTP /
  push heartbeats) isolating failures to a single component.
  → `03-monitoring/uptime-kuma/docker-compose.yml`, `03-monitoring/monitors/cake-monitor.sh`,
  `03-monitoring/monitors/packet-loss-monitor.sh`
- **Hardware / performance tuning** — headless thin-client (HP t630) deployment;
  CPU governor and AMD GPU forced to performance mode against headless
  downclocking.
  → `02-performance/gpu-performance/cpu-performance.service`,
  `02-performance/gpu-performance/gpu-performance.service`,
  `02-performance/gpu-performance/99-amdgpu-performance.rules`
- **Remote access** — SSH, xrdp, NoMachine; reachable over the WireGuard subnet.
  → `04-user-services/remote-desktop/server.cfg`, `01-core-network/ufw/setup.sh`

---

## B. Automation, Scripting & Tooling

- **Bash** — idempotent provisioning and monitoring scripts (`set -euo
  pipefail`, delete-before-add idempotency, PCRE parsing, curl push reporting).
  → `02-performance/cake/setup.sh`, `01-core-network/ufw/setup.sh`,
  `03-monitoring/monitors/packet-loss-monitor.sh`, `03-monitoring/monitors/cake-monitor.sh`
- **Scheduling** — cron-driven monitors feeding a push-based dashboard.
  → `03-monitoring/monitors/packet-loss-monitor.sh`, `03-monitoring/monitors/cake-monitor.sh`
- **Python**, **SQL**
- **Git / GitHub** — feature-branch and pull-request workflow (visible
  throughout this repo's history).
- **VS Code**
- **REST API integration**; **Claude API integration** for compliance workflows
- **Infrastructure-as-config** — the entire repo is a version-controlled config
  snapshot and rollback target; every file maps to a documented deploy path.
  → `CLAUDE.md`, `README.md`, `INSTALL-NOTES.md`

---

## 1. Professional background (beyond this repo)

Domain skills from prior work, not exercised by this project but part of the
broader toolkit:

PensionPro; Salesforce (custom dashboards, validated reports, workflow
automation); advanced Microsoft Excel (XLOOKUP, macros, pivot tables); ESOP
administration software; TValue 6 (amortization); Microsoft Access; SharePoint;
Microsoft Office Suite.
