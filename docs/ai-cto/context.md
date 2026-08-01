# AI CTO Context — localDNS

Read alongside the portfolio hub: `DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.

**Last updated:** 2026-08-01

---

## Default next actions

The pre-computed answer to "what's next?" — so a fresh session lands on a ready
queue instead of re-deriving it from the open-items table. This is the default
starting point; when the founder names a different priority, follow that instead.
Keep this block in sync when an item ships (mark it done, promote the next one).

**Ship path — the P1 chain (each unblocks the next; run in order).**

1. **Deploy the nftables volume populator to the t630.** This is the top of the
   chain — the by-category GB figures the Statements omit stay omitted until it
   runs. Follow CLAUDE.md § F end to end (`scp` the `collect/` tools → `nft -f`
   the ruleset → dry-run then `--apply` the populator → add the two cron lines).
   *Blocked on:* SSH to the t630 (`192.168.1.118`).
2. **Test the Statement PWA install on iOS and Android.** Confirm the
   `docs/statements/` gallery (commit `6134824`, merged but never tested on a real
   device) installs and opens offline as a home-screen PWA. *Blocked on:* the
   nftables deploy (step 1), so the installed gallery shows real data.
3. **Generate the first real Statement for a real household.** The end of the
   chain — the first document that ships for money. Honor the honesty invariant:
   only numbers the box actually measured (omit the neighbor benchmark and the
   by-category breakdown until step 1's data exists). *Blocked on:* a client data
   file (from Stage 05/08 in the DESIGN repo) + steps 1–2.

**Repo-hygiene path — close the "drift to reconcile" gap (independent of SSH).**
The repo is not yet a complete rollback target. Snapshot these live-but-uncommitted
pieces (or trim the references), newest-relevant first — see CLAUDE.md § C:

- `01-core-network/unbound/local-records.conf` — the LAN `*.home.lan` A-records
  drop-in (smallest, fully specified in CLAUDE.md § D; do this first).
- the **secrets vault** (sops + age) — sealed `*.env.sops`, `.sops.yaml`,
  `seal.sh`/`unseal.sh`; the pihole/router/ttyd credentials depend on it.
- `04-user-services/console/` — High-Seat launcher + the three `ttyd` unit files.
- `04-user-services/ai-orchestration/` — LiteLLM `docker-compose.yml`, `config.yaml`,
  `langgraph-router/` (the Odin supervisor).

Everything below (P2/P3) waits on physical access to the box or on the ship path
landing first — see the open-items table for the full list and blockers.

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
