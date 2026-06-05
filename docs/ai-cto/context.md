# AI CTO Context — localDNS

Read alongside the portfolio hub: `DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.

**Last updated:** 2026-06-05

---

## What this repo is

The live HP t630 configuration snapshot AND the Statement artifacts under `docs/statements/`. This is the product — public. The live t630 at 192.168.1.118 is the source of truth; this repo is the rollback target.

## Current state

| Component | Status | Notes |
| --------- | ------ | ----- |
| Unbound | Running | DoT split working; DNSSEC verified |
| Pi-hole v6 | Running | `network_mode: host`; upstream locked to `127.0.0.1#5335` |
| WireGuard wg0 | Running | VPN peer DNS resolved (host-net fix applied) |
| Uptime Kuma | Running | Host-networked; reachable from WG tunnel |
| CAKE QoS | Running | 85 Mbit on `enp1s0` |
| Statement PWA | Merged, not deployed | Commit 6134824; not tested on real device |
| nftables volume populator | Scaffolded, not deployed | Blocking per-category data in statements |
| LLM router (LiteLLM) | Config in repo, not deployed | Stage 10: fronts local Ollama on the t630 + cloud overflow; routes whole models, no sharding; t630 is CPU-only |

## Open items

| Item | Priority | Blocked on |
| ---- | -------- | ---------- |
| Deploy nftables volume populator to t630 | P1 | SSH to t630 (192.168.1.118) |
| Test Statement PWA install on iOS and Android | P1 | Depends on nftables deploy |
| Generate first real Statement for a real household | P1 | Client data file (from Stage 05/08 in DESIGN) |
| Identify or remove WG peers 10.8.0.4–6 | P2 | Physical access / device identification |
| Rotate Windows laptop WireGuard key | P2 | Physical access |
| Verify live Pi-hole upstream after volume migration | P2 | Next deploy cycle |
| Stand up LLM router on t630 (install Ollama, pull models, start LiteLLM) | P3 | SSH to t630 + an Anthropic API key for the overflow tier |

## Key file locations (repo → system)

See CLAUDE.md deploy table for the full map. Critical ones:

| Repo path | System path |
| --------- | ----------- |
| `01-unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` |
| `02-pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` |
| `05-wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` |
| `docs/statements/` | Served via GitHub Pages |

## Architecture pointers

- `CLAUDE.md` — authoritative briefing; start there every session
- `network-context.md` — design rationale for non-obvious decisions
- `docs/statements/` — Statement output directory (client + operator HTML)
- `01-unbound/streaming-forward.conf` — the DNS split decision point
- `01-unbound/tuning.conf` — single source of truth for cache/TTL/threading
