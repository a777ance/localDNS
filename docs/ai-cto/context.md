# AI CTO Context — localDNS

Read alongside the portfolio hub: `DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.

**Last updated:** 2026-08-01

---

## Default next actions

Pre-computed session-start queue — don't re-derive it. Do the top unblocked item.
Rationale lives in CLAUDE.md § F / § C and the open-items table below; don't restate
it here. Override only when the founder names a different priority. When an item
ships, tick it and promote the next.

**Do this (SSH to t630 `192.168.1.118` available):**

1. Deploy the nftables volume populator → run CLAUDE.md § F end to end.
2. Test the Statement PWA install (commit `6134824`) on iOS + Android.
3. Generate the first real Statement — measured numbers only (honesty invariant).

**Else (no SSH — close the repo-drift gap, see CLAUDE.md § C):**

1. Snapshot `01-core-network/unbound/local-records.conf` (spec in CLAUDE.md § D).
2. Snapshot the secrets vault (sops+age): `*.env.sops`, `.sops.yaml`, `seal.sh`/`unseal.sh`.
3. Snapshot `04-user-services/console/` (launcher + 3 `ttyd` units).
4. Snapshot `04-user-services/ai-orchestration/` (LiteLLM compose/config + `langgraph-router/`).

P2/P3 items (physical access, later deploy cycles) — see the open-items table.

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
| AI gateway (LiteLLM) + Open WebUI | Config in repo, not deployed | **Stage renamed `10-llm-router` → `10-ai-orchestration`.** LiteLLM (ai.home.lan:4040) fronts local Ollama + cloud tiers (now incl. cloud-explore/code/vision); Open WebUI (chat.home.lan:3000) browser UI; routes whole models, no sharding; t630 is CPU-only |
| Console / high seat (`11-console/`) | Config in repo, not deployed | **New Step 13.** Static launcher (`console.home.lan:8088`) pinning every realm + two `ttyd` web terminals — thin client (`term.home.lan:7681`) and laptop via the t630 as SSH-jump (`laptop.home.lan:7682`). Host-side systemd; UFW-gated LAN+WG only (a web shell — never WAN). The browser-as-Odin sidebar/persistence config is `11-console/browser-odin.md`. Laptop SSH target ships as a `CHANGE_ME`. |
| Odin orchestration layer (`10-ai-orchestration/langgraph-router/`) | Design + self-tested, not deployed | LangGraph supervisor **Odin** (alias Lionheart) above the front door: deterministic privacy gate (Heimdall), 3 orders of 5 + bound adversarial critic (Loki), Frigg (PII redaction), Hoard-Warden (spend cap), Huginn RAG (Mímir's well — local embeddings via the front door, needs `local-embed`/`nomic-embed-text`), Muninn (resume). `setup.sh` + `odin` CLI provided. Deterministic safety logic runs stdlib-only (`--selftest`); a live run needs `pip install -r requirements.txt` + the front door. The flat `dispatcher.py` remains the dumb-switch default. Lore in `docs/chronikonomicon/the-alliance-codex.md`. |

## Open items

| Item | Priority | Blocked on |
| ---- | -------- | ---------- |
| Deploy nftables volume populator to t630 | P1 | SSH to t630 (192.168.1.118) |
| Test Statement PWA install on iOS and Android | P1 | Depends on nftables deploy |
| Generate first real Statement for a real household | P1 | Client data file (from Stage 05/08 in DESIGN) |
| Identify or remove WG peers 10.8.0.4–6 | P2 | Physical access / device identification |
| Rotate Windows laptop WireGuard key | P2 | Physical access |
| Verify live Pi-hole upstream after volume migration | P2 | Next deploy cycle |
| Stand up the AI gateway on t630 (install Ollama, pull models, start LiteLLM at stage `10-ai-orchestration`) | P3 | SSH to t630 + an Anthropic API key for the cloud tiers |
| Stand up the console on t630 (`apt install ttyd`, place page + 3 systemd units, set `User=`, fill `/etc/a777ance/ttyd.env`, re-run UFW) | P3 | SSH to t630 + a stable laptop SSH address (its WireGuard IP or a DHCP-reserved LAN IP) |
| Run the Odin supervisor live (venv + `pip install -r 10-ai-orchestration/langgraph-router/requirements.txt`, point at the front door) | P3 | The gateway being up first |

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
- `10-ai-orchestration/langgraph-router/` — the Odin supervisor (README has the full roster)
- `10-ai-orchestration/ORCHESTRATION-BLUEPRINT.md` — the dumb-switch vs. supervisor design split
