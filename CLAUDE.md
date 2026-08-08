# CLAUDE.md

Briefing for Claude Code. Read this first — it is the authoritative summary of
the whole system. README.md is the top-level map and links out to the interactive
field guide. docs/architecture/network-context.md has detailed rationale for
non-obvious design decisions.

---

## House style: ordering & typography

These conventions apply across **every** A777ance repo — current and future. (Adopted 2026-06-05.)

- **Time-based content reads newest-first (reverse-chronological).** Logs, changelogs,
  decision logs (ADR / FIN), known-issues and issue trackers, FAQs, metrics and review
  logs, and "Handled For You" entries all lead with the most recent item. Apply this
  within the time-based *section* even when the whole file isn't time-based.
- **Alphabetical lists run Z → A** (descending).
- **Walkthroughs: reverse the blocks, keep the steps.** In a step-by-step guide, present
  the major sections/blocks in reverse order (last block first — it helps "block" the
  work), but keep the numbered steps *within* each block in forward order so every
  procedure stays followable. A walkthrough's table of contents mirrors the reversed
  block order. **Never renumber** — step and stage numbers stay fixed, so the intended
  execution order is always readable from the numbers.
- **Font: Gill Sans MT everywhere.** Every surface — customer-facing or internal — uses
  Gill Sans MT. Web/CSS stack:
  `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

---

## Portfolio conventions (all A777ance repos)

Shared rules distilled from the sibling A777ance repos. They govern this repo too —
especially the customer-facing **Statements** it owns under `docs/statements/`.

- **This is the *public* product repo — it holds the stack and the Statements.** The
  business model, pricing, guild economics, and real customer data live in **separate,
  private** repos. **Invariant:** never copy private/business/customer data here — real
  names and figures never appear in public git.
- **Honesty of the kept document.** A Statement ships for money only with numbers the box
  actually measured. Omit the "How You Compare" neighbor benchmark and the by-category GB
  breakdown (measuring layer scaffolded — see section F — not yet stood up) rather than
  print unsupported figures. People keep these documents — never fake a number on one.
- **Plain-English voice on customer-facing surfaces.** The Statements read the way a good
  tradesperson talks to a homeowner, not how an IT person talks to a server ("your
  living-room TV," not "the endpoint") — a grandparent should understand it. Internal docs
  may use jargon; the Statements may not.
- **No secrets in git.** Keys, passwords, and tokens live in the sops+age vault or `.env`
  (git-ignored); the repo ships `.env.example` / `CHANGE_ME` placeholders. Never commit the
  real thing.

---

## Contents

- [House style: ordering & typography](#house-style-ordering--typography)
- [Portfolio conventions](#portfolio-conventions-all-a777ance-repos)
- [0. What this repo is](#0-what-this-repo-is)
- [A. Hardware](#a-hardware)
- [B. Network topology](#b-network-topology)
- [C. Deploy paths](#c-deploy-paths)
- [F. nftables volume layer — deploy checklist](#f-nftables-volume-layer--deploy-checklist)
- [D. Unbound config](#d-unbound-config)
- [E. AMD Carrizo GPU](#e-amd-carrizo-gpu)
- [G. LLM sampling doctrine — the Jury](#g-llm-sampling-doctrine--the-jury)
- [H. Bifrost — command schema (loads every session)](#h-bifrost--command-schema-loads-every-session)
- [1. Known issues](#1-known-issues)
- [2. Verification](#2-verification)
- [3. Working philosophy](#3-working-philosophy)
- [4. Further reading](#4-further-reading)
- [5. AI CTO state](#5-ai-cto-state)

---

## 0. What this repo is

Config snapshot and rollback target for a self-hosted DNS + monitoring + VPN
stack on an HP t630 thin client. Every file maps to a specific location on the
live system (see "Deploy paths" below). Edits here do not take effect until
manually deployed.

**The live t630 is the source of truth.** When in doubt, SSH to `192.168.1.118`.

---

## A. Hardware

- **HP t630** — AMD Carrizo GX-420GI quad-core, 16 GB RAM, 16 GB eMMC
- **OS:** Ubuntu 24.04.4 LTS, kernel 6.17 series
- **NIC:** `enp1s0` (wired only — Wi-Fi disabled)

---

## B. Network topology

```
ISP (Spectrum ~200/100 Mbps asymmetric)
  │
  └── Netgear R7000     192.168.1.1    main router (routing, NAT, DHCP, WAN)
        │
        └── t630        192.168.1.118  DNS + VPN server (DHCP reservation)
              │
              └── wg0   10.8.0.1/24   WireGuard tunnel interface
```

**WireGuard peers**

| Peer | Tunnel IP | Notes |
| ---- | --------- | ----- |
| t630 wg0 | 10.8.0.1 | Server gateway; DNS address peers use |
| iPhone | 10.8.0.2 | |
| Windows laptop | 10.8.0.3 | Key rotation needed — see Known issues |
| (unidentified) | 10.8.0.4–10.8.0.6 | In wg0.conf, no recent handshake — identify or remove |
| Mac | 10.8.0.7 | |

**Services**

| Service | Runtime | Port(s) | Accessible from |
| ------- | ------- | ------- | --------------- |
| Pi-hole | Docker host-net | 53 (DNS), 8080 (UI) | LAN + WG subnet |
| Unbound | host OS | 5335 | Pi-hole only (via `127.0.0.1`) |
| Uptime Kuma | Docker host-net | 3001 | LAN + WG subnet |
| WireGuard | host OS | 51820/UDP | Internet (open to Anywhere) |
| NoMachine | host OS | 4000 | LAN only |
| xrdp | host OS | 3389 | LAN only |
| SSH | host OS | 22 | LAN + WG subnet |
| LLM router (LiteLLM) | Docker host-net | 4040 | LAN + WG subnet |
| Open WebUI (LLM chat UI) | Docker host-net | 3000 | LAN + WG subnet |
| Console launcher ("high seat") | host OS (systemd) | 8088 | LAN + WG subnet |
| ttyd web terminal — thin client | host OS (systemd) | 7681 | LAN + WG subnet |
| ttyd web terminal — laptop (SSH jump) | host OS (systemd) | 7682 | LAN + WG subnet |

**Pi-hole upstream DNS:** a single upstream — `127.0.0.1#5335` (Unbound on the host;
reachable directly because Pi-hole runs `network_mode: host`). Pi-hole does no
resolver selection of its own; it forwards every query to Unbound. Set via
`FTLCONF_dns_upstreams` in the compose file (Pi-hole v6 re-applies and locks it on
every start; visible read-only in the UI under Settings → DNS). Do not add public
resolvers here — that would race them for all queries and leak personal lookups.

**DNS resolution strategy (the split lives in Unbound):** `streaming-forward.conf`
is the single decision point. High-volume/low-sensitivity domains (Netflix,
YouTube, Spotify, Steam, etc.) are forwarded to **Cloudflare over DNS-over-TLS**
(`1.1.1.1@853#cloudflare-dns.com` / `1.0.0.1`, `forward-tls-upstream: yes`), so the
ISP sees an encrypted channel instead of cleartext lookups — trading privacy for
speed on traffic whose destination is not sensitive. Everything else (personal,
sensitive, default) resolves recursively through Unbound with DNSSEC — Cloudflare
never sees these queries. **Invariant:** never add sensitive domains to the
forward-path; that would hand Cloudflare your private lookups. (This path previously
forwarded to a ~18-resolver plaintext UDP/53 pool, which leaked streaming lookups to
the ISP in the clear. An interim plan to run a local `cloudflared proxy-dns` daemon
was dropped — Cloudflare removed that feature in v2026.2.0 — in favor of Unbound's
native DoT. See docs/architecture/network-context.md "Unbound DNS split".)

**Host's own DNS:** the t630 resolves its *own* queries (apt, git, curl) via external
resolvers (`01-core-network/host-dns/host-dns.conf`), NOT its own Pi-hole. Host-net Pi-hole takes
`0.0.0.0:53` (so the resolved stub is disabled, `DNSStubListener=no`), and
`/etc/resolv.conf` can't carry Unbound's `:5335` — so the host points straight at
`9.9.9.9`/`1.1.1.1` instead. See docs/architecture/network-context.md "Host resolver" for the root cause.

**Uptime Kuma** runs with `network_mode: host` so it can reach Unbound at
`127.0.0.1:5335` directly. No `ports:` mapping in the compose file. Pi-hole is
host-networked for the same reason (and so it answers VPN peers over `wg0`), so
both containers sit directly on the host network stack.

---

## C. Deploy paths

Files are grouped into **four service categories**, not installation order. The
category number is a rough build sequence (core network → performance → monitoring →
user services), but a file's real destination is defined by the table below — map
repo path → system path here, don't infer it from the number. Setup steps (router,
Docker CE, etc.) now live in the interactive field guide linked from README, not as
numbered folders.

Every row below corresponds to a file that **actually exists in this repo**. For
components that are documented for the live box but not snapshotted here, see the
"drift to reconcile" note under the table.

This table is the repo→system→reload map; **`docs/DEPLOY-PROTOCOL.md` is the procedure
that uses it** to land one change safely (sync the checkout → diff → back up → validate
→ reload → verify the *effect*). Read the protocol before deploying a row by hand.

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `01-core-network/unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/local-records.conf` | `/etc/unbound/unbound.conf.d/local-records.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `01-core-network/unbound/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `01-core-network/unbound/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `01-core-network/unbound/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `01-core-network/unbound/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `01-core-network/pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
| `01-core-network/pihole/.env.example` | copy to `~/pihole/.env` (git-ignored), set `PIHOLE_WEBPASSWORD` | — |
| `01-core-network/host-dns/host-dns.conf` | `/etc/systemd/resolved.conf.d/host-dns.conf` | `sudo systemctl restart systemd-resolved` |
| `01-core-network/ufw/setup.sh` | run directly | `sudo bash 01-core-network/ufw/setup.sh` |
| `01-core-network/wireguard/wg0.conf` | `/etc/wireguard/wg0.conf` | `sudo systemctl restart wg-quick@wg0` |
| `01-core-network/wireguard/peer-template.conf` | reference only | — |
| `02-performance/cake/setup.sh` | `/usr/local/sbin/cake-setup.sh` | `sudo systemctl restart cake` |
| `02-performance/cake/cake.service` | `/etc/systemd/system/cake.service` | `sudo systemctl daemon-reload` |
| `02-performance/gpu-performance/gpu-performance.service` | `/etc/systemd/system/gpu-performance.service` | `sudo systemctl daemon-reload` |
| `02-performance/gpu-performance/cpu-performance.service` | `/etc/systemd/system/cpu-performance.service` | `sudo systemctl daemon-reload` |
| `02-performance/gpu-performance/99-amdgpu-performance.rules` | `/etc/udev/rules.d/99-amdgpu-performance.rules` | `sudo udevadm control --reload-rules` |
| `03-monitoring/uptime-kuma/docker-compose.yml` | `~/uptime-kuma/docker-compose.yml` | `cd ~/uptime-kuma && docker compose up -d` |
| `03-monitoring/monitors/packet-loss-monitor.sh` | `~/packet-loss-monitor.sh` (+ cron) | `crontab -e` |
| `03-monitoring/monitors/cake-monitor.sh` | `~/cake-monitor.sh` (+ cron) | `crontab -e` |
| `04-user-services/remote-desktop/server.cfg` | `/usr/NX/etc/server.cfg` | `sudo /usr/NX/bin/nxserver --restart` |
| `04-user-services/console/index.html` | `/opt/console/index.html` | `sudo systemctl restart console` |
| `04-user-services/console/console.service` | `/etc/systemd/system/console.service` | `sudo systemctl daemon-reload` |
| `04-user-services/console/ttyd-thinclient.service` | `/etc/systemd/system/ttyd-thinclient.service` | `sudo systemctl daemon-reload` |
| `04-user-services/console/ttyd-laptop.service` | `/etc/systemd/system/ttyd-laptop.service` | `sudo systemctl daemon-reload` |
| `04-user-services/console/ttyd.env.example` | `/etc/a777ance/ttyd.env` (git-ignored; `chmod 600`) | — |
| `04-user-services/console/browser-odin.md` | reference only | — |
| `04-user-services/endpoint-hardening/user.js` | `<firefox-profile>/user.js` (snap: `~/snap/firefox/common/.mozilla/firefox/<profile>/`) | restart Firefox |
| `04-user-services/ai-orchestration/docker-compose.yml` | `~/llm-router/docker-compose.yml` | `cd ~/llm-router && docker compose up -d` |
| `04-user-services/ai-orchestration/config.yaml` | `~/llm-router/config.yaml` | `cd ~/llm-router && docker compose up -d` |
| `04-user-services/ai-orchestration/.env.example` | copy to `~/llm-router/.env` (git-ignored), set `LITELLM_MASTER_KEY` (+ `ANTHROPIC_API_KEY` for overflow) | — |
| `vault/seal.sh` | run in `vault/` — encrypts `cleartext/*.env` → committable `*.env.sops` | `cd vault && ./seal.sh` |
| `vault/unseal.sh` | run on the t630 — writes each sealed secret to its `secrets.manifest` deploy path (chmod 600) | `cd vault && ./unseal.sh` |
| `vault/rotate-secrets.sh` | edit a sealed secret in place, or `--rekey` all to new age recipients | `cd vault && ./rotate-secrets.sh …` |
| `04-user-services/ai-orchestration/jury/jury.py` | run on the t630 (or any host with the key) — adaptive self-consistency voter for Kimi K3 (see section G) | `python3 jury.py deliberate …` / `… calibrate …` |
| `04-user-services/ai-orchestration/jury/.env.example` | copy to `…/jury/.env` (git-ignored), add `FIREWORKS_API_KEY` | — |
| `04-user-services/ai-orchestration/jury-claude/jury_claude.py` | Claude-backend Jury — imports the `jury/` voter, adds a `ClaudeSampler` (Anthropic SDK). Run on any host with a key (see section G) | `python3 jury_claude.py deliberate …` / `… calibrate …` |
| `04-user-services/ai-orchestration/jury-claude/.env.example` | copy to `…/jury-claude/.env` (git-ignored), add `ANTHROPIC_API_KEY` | — |
| `docs/statements/tools/collect/nftables-accounting.nft` | load with `sudo nft -f nftables-accounting.nft` | re-run anytime (idempotent) |
| `docs/statements/tools/collect/populate_sets.py` | `~/a777ance/collect/populate_sets.py` (+ cron `3 */6 * * *`) | `crontab -e` |
| `docs/statements/tools/collect/collect_stats.py` | `~/a777ance/collect/collect_stats.py` (+ cron `30 0 * * *`) | `crontab -e` |
| `tools/check-provenance.py` | run directly (validate provenance tags; fail on an unstaged `R`-tier deploy target, an `R`/`A` tag with no `verify:` route, or a malformed claim; `--strict` also requires full deploy-target coverage) | `python3 tools/check-provenance.py` |
| `tools/check-doctrine.py` | run directly (asserts §G's stated sampler values match `jury/jury.py` — constructor defaults, CLI defaults, and the keys actually sent) | `python3 tools/check-doctrine.py` |
| `tools/check-docs.py` | run directly (validate Markdown links + repo-path references across ALL docs; trips on legacy 1.x paths; asserts the Bifrost sweep string **and** the expansion template are byte-identical across their three surfaces and that the template reduces to the sweep; **and** that spec §1, `docs/bifrost.html`, and CLAUDE.md §H assign every glyph the same role) | `python3 tools/check-docs.py` |
| `04-user-services/ai-orchestration/briefing-block.md` | canonical source for the Bifrost section in **every** sibling repo's `CLAUDE.md` — edit here, never in the rendered copies | `python3 tools/sync-briefings.py --write` |
| `04-user-services/ai-orchestration/branch-policy-block.md` | canonical source for the branch-policy section (`Yggdrasil` / Well of Mimir) in **every** sibling repo's `CLAUDE.md` — edit here, never in the rendered copies | `python3 tools/sync-briefings.py --write` |
| `tools/sync-briefings.py` | run directly (renders both canonical blocks — Bifrost and branch policy — into every sibling repo's `CLAUDE.md`; bare/`--check` reports drift, `--write` fixes it; also asserts the condensed block and §H agree on glyph roles, and trips on the retired push-to-`main` directive) | `python3 tools/sync-briefings.py --write` |
| `tools/check-branch-cap.py` | run directly (no repo carries more than **9** branches; a `claude/*` ref already reachable from an `archive/*` branch counts as PENDING deletion and reports rather than fails; unreachable remotes are skipped and named) | `python3 tools/check-branch-cap.py` |
| `.claude/hooks/gate.sh` | `PreToolUse(Bash)` hook — runs the five checks above before any `git commit` and blocks on failure (bypass: `touch .claude/.gate-off`) | wired in `.claude/settings.json` |
| `tools/migrate.sh` | one-time 1.x→2.0 folder migration (already applied) | — |

**Drift to reconcile — documented for the live box but NOT in this repo snapshot.**
The README 2.0 architecture diagram lists these under `04-user-services/`, and the
sections below still describe their live behavior, but no config is checked in. Either
snapshot the config here (so the repo stays a valid rollback target) or trim the
reference:

| Missing from repo | What it should hold | Referenced in |
| ----------------- | ------------------- | ------------- |
| `04-user-services/ai-orchestration/langgraph-router/` | The Odin supervisor (LangGraph graph, `odin` CLI, `dispatcher.py`, juror/critic roster) — **still missing**; snapshot from the live box, don't fabricate from lore. The LiteLLM front door (`docker-compose.yml`, `config.yaml`, `.env.example`, `README.md`) and the `jury/` + `jury-claude/` voters (section G) are now snapshotted here. | topology services table, Known issues |
| **sealed** `vault/*.env.sops` | The sops+age **tooling** (`.sops.yaml`, `secrets.manifest`, `seal.sh`/`unseal.sh`/`rotate-secrets.sh`, README) is now snapshotted under `vault/`. **Still missing:** the actual sealed `*.env.sops` — create them from the real values on the t630 (`./seal.sh` after setting a real age recipient). | Known issues (pihole/router/ttyd secrets) |

**Docs relocated under `docs/`** (not root): `INSTALL-NOTES.md`, `SKILLS.md`,
`network-context.md`, `cell-grammar.md` → `docs/architecture/`; AI-CTO context →
`docs/ai-cto/`; the Network Activity Statement gallery + `collect/` tools →
`docs/statements/`.

---

## F. nftables volume layer — deploy checklist

Run this once on the t630 to stand up per-category byte accounting. All four
steps can be done in one SSH session.

```bash
# 1. Copy the collect tools to the box (from your machine)
scp -r docs/statements/tools/collect/ user@192.168.1.118:~/a777ance/collect/

# 2. Load the accounting ruleset (idempotent — safe to re-run)
sudo nft -f ~/a777ance/collect/nftables-accounting.nft
sudo nft list table inet a777acct          # sets + counters exist, all zero — expected

# 3. Dry-run the set populator (resolves DNS, touches nothing)
python3 ~/a777ance/collect/populate_sets.py | head

# 4. Apply for real (programs the IP sets; counters start counting)
sudo python3 ~/a777ance/collect/populate_sets.py --apply
sudo nft -j list counters table inet a777acct   # should show non-zero bytes within minutes

# 5. Add to cron (crontab -e)
# refresh IP sets every 6h (CDN IPs rotate; elements time out in 24h)
3 */6 * * *  sudo /usr/bin/python3 /home/USER/a777ance/collect/populate_sets.py --apply >/dev/null 2>&1
# collect monthly stats nightly
30 0 * * *   /usr/bin/python3 /home/USER/a777ance/collect/collect_stats.py \
             --out /var/lib/a777ance/$(date +\%Y-\%m).stats.json
```

Replace `USER` with the actual username on the t630. After the cron runs once,
verify with: `sudo nft -j list counters table inet a777acct`

---

## D. Unbound config

**Six** drop-ins live in `01-core-network/unbound/` in this repo, loaded
alphabetically (A→Z) by Unbound from `/etc/unbound/unbound.conf.d/` — listed Z→A
here per house style:

| File | Purpose |
| ---- | ------- |
| `tuning.conf` | All performance and cache values — single source of truth |
| `streaming-forward.conf` | Forward-zones: streaming/media domains → Cloudflare over DoT (`1.1.1.1@853`, `forward-tls-upstream`); all else recursive. Sets `tls-cert-bundle` for upstream cert validation. |
| `server.conf` | Interface, port, access-control, security flags |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `remote-control.conf` | Unix socket for `unbound-control` |
| `local-records.conf` | LAN-only A records (`ai`/`chat`/`console`/`term`/`laptop`/`kuma`/`pihole`.home.lan → the t630) so the console sidebar pins names not IP:ports; `local-zone … transparent` overrides only the names defined, not the whole zone. |

The `local-records.conf` names resolve only on the LAN/VPN (they point at the
t630's private `192.168.1.118`) and must never be published to a public resolver.
**Verify against the live box:** the names, IP, and `transparent` mechanism are
reconstructed from this documentation — confirm each `local-data` line matches the
t630 before trusting this drop-in as an authoritative rollback target.

`tuning.conf` is the only place to change cache sizes, TTLs, or threading.
Do not split these into separate files.

To verify the DNS split: `sudo unbound-control lookup netflix.com` should show
`forwarding request` to `1.1.1.1@853`/`1.0.0.1@853`. `sudo unbound-control lookup
chase.com` should show iterative delegation to authoritative nameservers (no
forwarder). A resolved `dig @127.0.0.1 -p 5335 netflix.com +short` confirms the DoT
path works end-to-end (it fails closed to recursion via `forward-first` if :853 is
blocked).

---

## E. AMD Carrizo GPU

The iGPU downclocks to ~200 MHz headless. Four pieces, all required:

1. GRUB: `amdgpu.dpm=1 amdgpu.runpm=0 processor.max_cstate=1`
2. `02-performance/gpu-performance/gpu-performance.service`
3. `02-performance/gpu-performance/cpu-performance.service`
4. `02-performance/gpu-performance/99-amdgpu-performance.rules` — re-asserts `high` on every DRM event

---

## G. LLM sampling doctrine — the Jury

How this stack drives its *own* models (Kimi K3 on Fireworks, reached through the
LiteLLM router). Adopted 2026-08-01. The unit of inference is **one tuned draw**;
reliability comes from **how many draws and how they're aggregated**, not from
making any single draw heavier.

**The pipeline — lazy anchor → governed-warm body → concurrent vote:**

- **Lazy anchor (first token).** Reasoning effort stays `low`. The first token is a
  cheap, honest reflex, not an effortful pre-committed conclusion — it must not
  anchor the trajectory into a rationalization. A detached "thinking" block can be
  unfaithful (it justifies an answer the model already picked); reasoning that is
  *load-bearing in the answer body* cannot be skipped. Prefer the latter — ask the
  model to derive in the open, not to hand back a thinking dump.
- **Governed-warm body (in-flight).** Run warm enough to self-correct mid-stream,
  but **always pair temperature with a tail-clip** so it can never sample garbage.
  Default juror config: `temperature 1.1`, `top_p 0.9`, `top_k 40`,
  `max_tokens 8192`, presence/frequency penalties **`0`** (penalties corrupt code
  and stack a second randomizer on the temperature — keep them off),
  `Reasoning History: interleaved`.
- **Concurrent vote (aggregate).** Never consume a single warm draw for anything
  that matters — it's an honest guess, not a verdict. Sample several and let
  agreement outvote the idiosyncratic rationalizations. Diverse-but-coherent draws
  are the fuel; a plurality vote is the governor.

**Invariants:**

- **Match every degree of temperature with a degree of governance** — a tail-clip
  (`top_p`/`min_p`) so it can't sample garbage, and a selector (the vote) so the
  diversity is filtered into quality. Ungoverned high temperature is the *least*
  intelligent setting on the panel, not the most.
- **Temperature is a variance dial, not an intelligence dial.** Its only job is to
  manufacture the decorrelated draws a vote needs. Too cold ⇒ near-identical draws
  ⇒ the jury collapses to one. Peak useful heat for voting is ~`0.8–1.1` *governed*;
  past the knee (~1.2) you buy incoherence, not insight.
- **Measure `p`, don't guess it.** Per-sample accuracy sets the jury size. Voting
  helps only when the correct answer is already *modal*; below that threshold it
  amplifies a wrong answer. Run `jury.py calibrate` to measure the real number on
  the task before trusting a vote.
- **Unanimity is not a confidence signal.** A 5/5 tally is *ambiguous* between a
  strong panel and a **collapsed** one: the synthetic study (`/diet`) shows that as
  draws correlate (`rho` → 0.9) the vote's lift decays to **Δ=+0.00** while `p̂` sits
  unmoved at ~0.68 — identical marginal accuracy, worthless vote. Correlated jurors
  agree *because* they're correlated. Never read agreement as evidence of
  correctness; only a measured `p̂` (and dispersion) can tell the two apart, which is
  what `calibrate` is for. On a keyless in-harness run, say which of the two you
  cannot rule out.
- **Never hand jurors the answer menu.** A supplied option set is a *shared prior* —
  it correlates the draws by construction and inflates agreement, exactly the Panel-B
  collapse above. Have each juror coin its own answer and tally by exact match on the
  free-form string; normalize only afterward, in the open. Reusing a previous run's
  menu to make tallies "comparable" is the same error with a second run's authority
  behind it. Force a fixed label set only when the question genuinely has one, and
  record that you did.

**Portability — the vote is the governor that survives vendor changes.** The
per-token knobs live in the *vendor's* layer, and vendors are removing them: some
frontier model families (e.g. the latest Gemini models, mid-2026) now ignore
`temperature`/`top_p`/`top_k`, steering variance through system instructions and
thinking-level settings instead. When a provider fixes or removes the decoding
knobs, source juror diversity **synthetically** — prompt/framing/persona variation,
or cross-model ensembling — and lean on the selector. Keep synthetic variants
**answer-preserving and quality-matched**, or they inject the systematic error a
vote entrenches. Temperature is a diversity source you may lose; the vote is one you
own — it sits in a layer no vendor can deprecate.

**The tool.** `04-user-services/ai-orchestration/jury/` implements this end to end —
an adaptive sequential voter that empanels jurors in concurrent batches and stops on
a Dirichlet posterior (easy prompts settle at `--min-n`, split ones run to
`--max-n`), plus a `calibrate` mode that measures `p̂` and separates dispersed-error
tasks (voting works, even below `p=0.5`) from systematic bias (voting entrenches the
wrong answer). Standard library only, offline `--mock` mode for keyless testing. See
its README.

A **Claude-backend variant** lives in `04-user-services/ai-orchestration/jury-claude/`:
it imports the same voter and swaps in a `ClaudeSampler` over the Anthropic SDK. One
honest deviation from this doctrine, stated in its README: current Claude models
**remove `temperature`/`top_p`/`top_k`** (400 on send), so there is no governed-warm
temperature to set — variance comes from native sampling stochasticity plus **adaptive
thinking** (the load-bearing "derive in the open" §G prefers), and `calibrate` becomes
the *only* variance control ("measure `p`, don't guess" applied to a platform where the
sampler, not a slider, sets `p`). The doctrine also runs **in-harness**: the `juror`
subagent (`.claude/agents/juror.md`) plus the `/cardio` command
(`.claude/commands/cardio.md`) empanel a concurrent jury of Claude Code subagents
and take a plurality — for one-off judgment calls where you'd otherwise consume a single
warm draw.

**Where these clauses live — a clause stated only here governs nothing.** This briefing
reaches a reader once, at read time; it is *not* in the read path of a run that edits the
sampler, writes a new agent, or tunes the router. An invariant whose only residence is
briefing prose therefore has an author and no **site**: the run's given-set omits it, and
silence in the file the run *does* read is not a gap but an assignment — nothing to check,
so nothing gets checked. Each clause is placed where the run that could break it will
actually meet it:

| Clause | Site |
| ------ | ---- |
| **Sampler values** — `temperature 1.1`, `top_p 0.9`, `top_k 40`, `max_tokens 8192`, penalties `0` | `jury/jury.py` **and** `tools/check-doctrine.py`, which fails if the two disagree |
| Synthetic diversity must be answer-preserving & quality-matched | `.claude/commands/cardio.md` · `jury-claude/jury_claude.py` |
| Measure `p̂`, don't guess it | `.claude/commands/form.md`, `.claude/commands/workout.calibrate.md` |
| Never consume a single warm draw; the vote is the governor | `.claude/commands/cardio.md`, `strength.md`, `workout.md` · `.claude/agents/juror.md` — restated inline, not merely cited |
| **Never hand jurors the answer menu** — free-form coinage, normalize after | `.claude/commands/cardio.md`, `workout.md` · `.claude/agents/juror.md` — restated inline |
| **Unanimity is unpriced** — agreement is not confidence; name what is not certified | `.claude/commands/cardio.md`, `workout.md` — a mandatory bound line, not an optional caveat |
| Lazy anchor — first token ASAP, low effort | `.claude/hooks/refeed.sh` (injected at `SessionStart`, so it enters every session's given-set) · `.claude/agents/juror.md` |

The first row is the strongest form available: a clause that decides **mechanically** gets a
static check, which holds no matter which file the run read and fails loudly instead of
silently. The rest decide by judgment, so restatement in the command file is the site — cite
`§G` *alongside* the restated rule, never *instead of* it, because a subagent's context is
its own and a pointer it cannot follow assigns nothing. **When adding a §G clause, site it
before treating it as landed.**

**The worked reference.** `04-user-services/ai-orchestration/examples/workout-bootstrap-paradox-session.md`
keeps two runs of the same prompt, newest-first, as the standard for how an in-harness
Jury run reports its own bounds: a **2026-08-07** menu-free reproduction (free-form labels,
4/5 exact-match, bounded by the `/diet` collapse regime) above the original **uncalibrated**
run whose two honesty flags it fixes. Read it before reporting any jury result — the point
of the file is what it *declines* to certify.

---

## H. Bifrost — command schema (loads every session)

**Bifrost is the A777ance command-composition schema. It loads with this briefing, so it is
active — and to be *followed* — from the first token of every session:** adopt the `~`
lazy-anchor posture (§G) at session start — first token ASAP, the *model* stays high,
continuity coalesces mid-flight — and read Bifrost notation per this schema whenever the
founder uses it. A keyboard-spatial notation: hold `Shift` and sweep the number row
`!@#$%^&*()` left→right; each glyph is an *archetype* (a role) fulfilled by slash commands +
a plain-language sub-prompt.

- **Backbone:** `'` ignition (begins the Bifrost) · `~` continuity/lazy-anchor · `` ` ``
  descriptor (and, bare, the *expansion call*) · `!` cargo (a *manifest*) · `@` source —
  **read-only** · `#` repo/destination — **write-allowed** · `$` sanity · `%` compliance ·
  `^` cars/lanes · `&` rotary — the **rabbit trail**, a nested Bifrost (also the sequential
  form) · `*` stop signal (red by default) · `()` governance (release conditions). Off-row
  `'`/`~`/`` ` `` stage; keys 1–4 **Preload** — a complete manifest (*what · from where · to
  where · against what*); `%` (key 5) **gateway**; keys 6–0 **Travel**.
- **`@`/`#` are a permission pair, not a pair of arrows** (founder's rule, 2026-08-08). `@` is
  **read-only** — everything under it may be read and must not be written. `#` is
  **write-allowed** — what this run may create, modify, or overwrite (still two-way; you read
  back from it). **They may overlap:** `@` alone = read-only, `#` alone = writable, both =
  read-write. Two slots, three states, one **mount table**. This keeps `@` reading and `#`
  writing, so every string already written stays valid — it only *adds* the guardrail, and gives
  the one-way door a question with an answer: *is every write in this chunk inside `#`?*
- **`'` is always the signal to begin the Bifrost** (founder's rule, 2026-08-07 — fixes a mobile
  bug). Treat `'`, `'` (curly) and `′` as the same glyph, and treat **presence and absence as
  the same string**: `' ~ !…` ≡ `~ !…`, `''` ≡ `'`. It marks *where* the Bifrost starts, never
  *what* runs, so it takes no sub-prompt, no `/how`, no intensity dial, and scores `0`
  turbulence. A letter-flanked `'` (`don't`, `founder's`) is prose in a sub-prompt, not an
  ignition — only a free-standing `'` ignites. Never ask which apostrophe the phone chose.
- **A bare `'` (the whole message) = the reference call. Return this string and NOTHING else:**

  <!-- bifrost-sweep:start — canonical copy; tools/check-docs.py fails if the mirrors drift -->
  ```text
  ~!@#$%^&*()
  ```
  <!-- bifrost-sweep:end -->

  It is **the sweep itself** — exactly what sliding your finger down the row on a laptop puts on
  the screen. Not a legend, not a glossary, not a table: the row. So it is a **lookup, not a
  generation** — same bytes every call, every session, every model. No preamble, no trailing
  offer, no adaptation to the conversation. Answer *immediately*; it reads no file and fires no
  cargo. **§G is out of scope, stated per §3:** §G governs *inference* and a constant involves
  none — no `p` to measure, nothing to vote on, no draw to govern. Two details worth knowing:
  `` ` `` is absent because `Shift` on that key **is** `~` (you cannot sweep it and shift it at
  once), and this sweep leads with staging `~` while the **Golden Rule** used for turbulence
  scoring stays `!@#$%^&*()` — staging glyphs are off-road. The glyph *meanings* live in the §H
  backbone above and in the spec's §1 table; the reference call hands back the **order**, which
  is the thing a phone cannot sweep for itself.
- **A bare descriptor — `` `…` `` with no backbone glyph in the message — is the *expansion
  call*.** The backticked text is a **seed**, and the answer is one complete, schema-compliant
  line with **every backbone slot filled in**, for the founder to read, parse and tweak. Fill
  this skeleton:

  <!-- bifrost-template:start — canonical copy; tools/check-docs.py fails if the mirrors drift -->
  ```text
  ~ (fill in) ! (fill in) @ (fill in) # (fill in) $ (fill in) % (fill in) ^ (fill in) & (fill in) * (fill in) ( (fill in) )
  ```
  <!-- bifrost-template:end -->

  **The skeleton is the sweep, spaced** — strike the `(fill in)` slots and the whitespace and
  `~!@#$%^&*()` remains; `tools/check-docs.py` asserts that identity, so template and sweep can
  never drift. `'` hands back the **order**; `` `seed` `` hands back the order **with the slots
  filled**. Rules: echo the seed back on the `` ` `` line (so the founder sees what was *read*);
  fill **every** slot, never drop one (a complete draft is edited *down* — an omitted slot is a
  silent decision); emit in Golden Rule order, so `K = 0` by construction; **`*` comes back RED,
  always** — an expansion is a *proposal*, nothing ran and no `#` was touched; and **collapse
  it** — where the surface renders HTML (chat, GitHub Markdown, the page) ship it inside a
  `<details>` whose `<summary>` is the `~` requirement line, plain fenced block otherwise. With
  a backbone glyph present, `` ` `` is the ordinary descriptor — unchanged. An empty descriptor
  returns the sweep. **§G applies in full here** (unlike the bare `'`, which returns a constant):
  an expansion *composes*, so lazy anchor → governed-warm body → selector — with the deviation
  stated per §3, the selector is the **human at the `*` gate**, not a jury. Want the vote anyway?
  Put it in the cargo: `! /cardio`.
- **`` ` `` and `&` are the same operation — nesting, at two positions** (founder's rule,
  2026-08-08). `&` is the **rabbit trail**: a digression you *come back from*, opening another
  full Bifrost inside this one. `` ` `` nests at staging, `&` nests on the road —
  `` `seed` `` ≡ `& seed` hoisted to position zero, which is why a bare descriptor can generate
  a line at all. So **expansion is recursive by construction** (any `&` in an expanded line is
  itself a seed), and `&`'s "sequential" reading is just nesting seen from the parent's frame.
  Turbulence still treats them differently and correctly: `` ` `` is staging and scores `0`;
  `&` holds position 7 and scores.
- **The greater traffic light is always the last bulwark** (founder's rule, 2026-08-08). Every
  nest **adds** a light; none removes one. An inner `*` going green releases its chunk **into
  its parent**, never into the world — only the outermost `*` stands between a `!` and an effect
  that cannot be recalled, and it stands no matter how many inner gates already cleared.
  Governance is a conjunction down the whole chain, so an inner gate can never be more
  permissive than the one above it. Stated as a pair: **permissions intersect inward, gates
  conjoin outward** — a nested road may never write outside its parent's `#`, nor release past
  its parent's `*`. That is what lets `~` stay reckless at any depth: **nesting multiplies the
  reasoning, never the exposure.**
- **`~` is the §G lazy anchor:** fire the first token ASAP (very low effort — the *model*
  stays high), and let continuity coalesce **mid-flight**; more `~` = lazier.
- **`*` cuts the road into Dispensations.** Each chunk is bounded and self-governing; `()`
  states what must hold before the next opens. Governance has three outcomes — satisfied,
  **re-flagged** (return upstream via `&` — this is what makes a fixed string produce unbounded
  output), or unsatisfiable (eject to the shoulder). **The one-way door:** `~` rushes the
  reasoning, `*` gates the *effects* — irreversible cargo (share/publish/deploy) rides past a
  light, which is exactly what makes the lazy start affordable.
- **Guardrails survive a keyboard-mash:** `~` continuity, `$` sanity, `%` compliance — plus
  `*()` **governance**, the only one that repeats at every chunk boundary.
  `+` / repetition = more; `-` inverts into a stress test.
- **Cars:** explicit `^` always beats inferred. With no `^`, `!`'s command arity instantiates
  lanes 1:1; with `^` present, `^` sets the lanes and `!`'s commands are the per-lane pipeline.

**Status:** notation only — no dispatcher parses it yet. Full spec (glyph table, grammar,
physics, MASH turbulence, worked examples, changelog):
`04-user-services/ai-orchestration/highway-notation.md` · rendered page:
<https://a777ance.github.io/localDNS/bifrost.html>.

---

## 1. Known issues

| Issue | Action |
| ----- | ------ |
| Console web terminals are a login shell over HTTP | `04-user-services/console` (not yet snapshotted — see section C drift note) exposes `ttyd` on 7681 (thin client) and 7682 (laptop, via the t630 as SSH jump). The `ttyd` `--credential` is the only gate to a shell — treat it like a root password (in `/etc/a777ance/ttyd.env`, `chmod 600`, never in git). **LAN + WG only — never port-forward 8088/7681/7682; remote access is through WireGuard.** Harden with TLS (`ttyd -S`) and OS `login` over `bash` (notes in the unit files / `04-user-services/console/README.md`). |
| Laptop SSH target is a placeholder | `04-user-services/console/ttyd.env.example` ships `LAPTOP_SSH=CHANGE_ME@10.8.0.CHANGE_ME`. Point it at a **stable** address (the laptop's WireGuard IP or a DHCP-reserved LAN IP), not a floating lease, or the laptop terminal won't connect. |
| Heavy DeepSeek-R1 on local CPU overheats the client | Don't run `deepseek-r1:7b`+ on a CPU — its long chain-of-thought pins every core for minutes (cooks a laptop, throttles the t630). `04-user-services/ai-orchestration/config.yaml` (not yet snapshotted — see section C drift note) now ships a reasoning ladder: `local-reason` (deepseek-r1:1.5b, t630 CPU, cool) for light work and `cloud-gpu-reason` (full R1 on a rented GPU via Tailscale, spun up on demand) for heavy work, falling over to `cloud-overflow` when the pod is off. See `04-user-services/ai-orchestration/README.md` "Offload heavy reasoning to a rented GPU." |
| Live Pi-hole upstreams ≠ repo | Pi-hole v6 re-applies & locks `FTLCONF_dns_upstreams: 127.0.0.1#5335` on every start, overriding any `172.17.0.1#5335`/public resolvers left in the `pihole_data` volume. Confirm in the UI after deploying onto an old volume. |
| Host-net Pi-hole vs systemd-resolved `:53` | Host-net Pi-hole binds `0.0.0.0:53`, colliding with the resolved stub on `127.0.0.53:53`. `01-core-network/host-dns/host-dns.conf` now sets `DNSStubListener=no` and the field-guide DNS steps re-point `/etc/resolv.conf` off the stub. On the live box, check current state before re-applying (see docs/architecture/INSTALL-NOTES.md item 13). |
| VPN peer DNS over the tunnel | **Resolved.** Pi-hole switched to `network_mode: host` — Docker DNAT no longer in the path, so `10.8.0.1:53` is answered directly for queries sourced from `wg0`. Port 8080 also added to the WG UFW rules so the Pi-hole UI is reachable from VPN peers. |
| WireGuard `::/0` IPv6 black hole | Server is IPv4-only in-tunnel; peers routing `::/0` black-hole IPv6 (handshake OK, pages hang). Peer template now defaults to `0.0.0.0/0`. Leak-free dual-stack fix (ULA + NAT66) documented in docs/architecture/network-context.md "WireGuard IPv6 black hole". |
| WireGuard peers 10.8.0.4, 10.8.0.5, 10.8.0.6 | Present on the **live box** (real public keys) but still UNIDENTIFIED with no recent handshake — identify each device or remove the stale peer. The repo `01-core-network/wireguard/wg0.conf` represents them as commented placeholder `[Peer]` blocks (real keys never live in git). |
| Windows laptop WireGuard key | Exposed during setup; rotate before trusting this peer |
| Pi-hole v5 → v6 env vars | `pihole/pihole:latest` is v6; compose migrated from v5 vars (`WEBPASSWORD`, `WEB_PORT`, `PIHOLE_DNS_`) to `FTLCONF_*`. The v5 names are silently ignored by v6. |
| `FTLCONF_webserver_api_password` in pihole compose | Now sourced from `~/pihole/.env` (sops+age vault — not yet snapshotted, see section C drift note), fail-closed via `${...:?}` — no credential in git. Unseal the vault before `docker compose up`. |
| LLM router port vs NoMachine | The router (LiteLLM, stage 10) listens on **4040**, not LiteLLM's default 4000 — NoMachine already holds 4000 on this box. UFW gates 4040 to LAN + WG. |
| LLM router secrets (`~/llm-router/.env`) | `LITELLM_MASTER_KEY` + `ANTHROPIC_API_KEY` live in `.env` (git-ignored); repo ships `.env.example` with `CHANGE_ME`. Never commit the real keys. |
| Open WebUI port + first-run admin | Chat UI on **3000** (8080 is the Pi-hole UI). First account created at `chat.home.lan:3000` becomes admin — create it from a trusted device. State in `~/llm-router/open-webui-data/`. |

---

## 2. Verification

```bash
systemctl status unbound
dig @127.0.0.1 -p 5335 example.com +dnssec        # 'ad' flag = DNSSEC working
dig @127.0.0.1 -p 5335 netflix.com +short          # DoT forward-path resolves end-to-end
sudo unbound-control lookup netflix.com            # forwarding request → 1.1.1.1@853 / 1.0.0.1@853
sudo unbound-control lookup chase.com              # should show: iterative delegation
docker ps                                          # pihole + uptime-kuma both Up
systemctl is-active console ttyd-thinclient ttyd-laptop  # console + both web terminals active
dig @127.0.0.1 -p 5335 console.home.lan +short     # 192.168.1.118 (high-seat name resolves)
sudo wg show                                       # wg0 up, peers listed
sudo ufw status verbose                            # 51820/udp Anywhere; all else LAN
tc qdisc show dev enp1s0                           # cake bandwidth 85Mbit
sudo iptables -t mangle -L POSTROUTING -v | grep DSCP  # EF mark on sport 53
cat /sys/class/drm/card*/device/power_dpm_force_performance_level  # high
```

---

## 3. Working philosophy

Every commit that reaches `main` must leave README.md able to reproduce a working system
on clean Ubuntu 24.04. That is the condition for entering the Well (below) — on
Yggdrasil it is the target, at the Well gate it is binding.

**Yggdrasil and the Well of Mimir** — founder's standing instruction (2026-08-08),
superseding "push to `main`, no branches" (2026-06-05).

- **`Yggdrasil` is the one standing working branch. Always push there, never to `main`.**
  One super-branch for the whole portfolio, in every repo — no per-session branches. The
  branch-per-session habit is what produced 337 stale `claude/*` branches, 226 of them
  carrying commits that exist nowhere else.
- **`main` is the Well of Mimir** — vetted knowledge. It moves only by a PR that the
  founder approves. No cadence, no auto-merge: the Well fills when the founder decides it
  does. This is the Bifrost one-way door (§H) at portfolio scale — `main` is the outermost
  `*`, and no inner gate may release past it.
- **The spring is the founder, and it is out of scope for the machine.** An analog signal
  nothing here can sample or verify against. Yggdrasil and the Well are channels, not
  sources; every file in this repo is *transmission*, and transmission never promotes
  (Provenance Ladder, below). A green check proves transcripts agree with **each other** —
  never that they agree with the founder. Only asking closes that gap.
- **Never overwrite doctrine.** Pull with `--ff-only` and nothing else — a fast-forward
  can only add commits, where a merge, rebase, or reset can silently rewrite founder-
  authored text. A session transcribes doctrine; it does not author it.
- **The tree is bigger than GitHub.** Yggdrasil spans the interacting systems — the
  t630 stack, the LiteLLM router, the NotebookLM bridge, Stripe, Setmore, the CRM — and
  GitHub is one root-well it drinks from. That is why the seed flows well→tree at
  `SessionStart` and tree→well at the PR gate.
- **Never more than 9 branches in a repo** — founder's standing instruction (2026-08-08),
  enforced by `tools/check-branch-cap.py` at the commit gate. With `main`, `Yggdrasil` and
  the drawer, a healthy repo sits at 3–5; nine is headroom, not a target.
- **The doom drawer — "Didn't Organize, Only Moved."** Retire a branch by **putting it in
  the drawer first**: `doom-drawer/<date>`, an octopus commit whose parents are the stale
  tips, keeps every orphaned commit reachable from one ref, after which deleting the
  branches loses nothing. It is the ADHD filing trick applied to refs, and the name states
  the honest limit — the drawer is *findable*, not *sorted*. That is the point: sorting is
  what makes people throw things away, and 226 of the original 338 branches held commits
  that existed nowhere else. **Never delete a `claude/*` branch that is not reachable from
  a `doom-drawer/*` (or legacy `archive/*`) ref.** Open the drawer with
  `git log --oneline doom-drawer/* --not origin/Yggdrasil`; take something back out with
  `git branch <name> <sha>`.

**RCPS — how work gets done here** (adopted 2026-08-07). The acronym carries **two
readings, and both are required, interleaved**:

- **Root Cause Problem Solving** — fix the thing that *generated* the defect, not the
  defect. Every finding gets one question before any patch: *what produced this, and
  what else is it still producing?* A flaw in a run is a flaw in the routine that ran
  it; a wrong value on the box is a wrong value in the repo it deploys from.
- **Record · Commit · Push · Sync** — the fix isn't real until it is written down where
  the next session will read it, committed, pushed, and reconciled with the live box.
  An uncommitted insight is a rumor.

**Interleaved, not sequential.** Neither half counts alone: a root cause you don't
record regenerates the defect next session, and a recorded patch with no root cause
just moves it. So each pass runs *diagnose → fix the generator → record → push*, and
the record names the generator, not only the symptom. Where the generator is an
executable surface (`.claude/commands/*.md`, `.claude/agents/*.md`, a script, a unit
file), patch **that** — doctrine in prose is advisory; runs inherit their behavior from
the file that ran them, and any invariant not encoded there will be re-broken by
someone following the file correctly.

**Watch for inherited authority.** A kept artifact — a reference transcript, a prior
run's parameters, a "we've always done it this way" constant — accrues authority by
repetition alone. Ask where it entered from *outside* the loop; if the answer is "an
earlier copy of itself", it has no origin and you are cargo-culting a bootstrap
paradox. Worked case: `04-user-services/ai-orchestration/examples/workout-bootstrap-paradox-session.md`.

**An invariant needs a site, not an author.** This briefing is read once, by the
operator, at read time — it is outside the read path of every subsequent run, so an
invariant that lives *only here* assigns nothing to a run's given-set and will be
re-broken by a run following its own file faithfully. **A citation is not a site:**
`.claude/commands/cardio.md` cited § G five times while its own text defined the
confidence scale § G forbids, and the text won. And **silence is an assignment** — with
no confidence policy stated, a run reports closed by default, so the unknown state has
to be made mandatory, not merely permitted. Migration upward is the repair: mechanical
check → fail-closed structure → inlined text in the file that executes. Ranked sites,
the working-tree audit, and what is still unsited: `docs/architecture/warrant-sites.md`.
Rank-1 site for the repo's static checks: `.claude/hooks/gate.sh` (PreToolUse — blocks a
commit that fails `tools/check-docs.py` or `tools/check-provenance.py`; bypass with
`touch .claude/.gate-off`, which puts the invariant back to having no site).

**The Provenance Ladder governs that check** — the full grammar, gates, and failure
catalogue live in `docs/provenance.html` (published at
<https://a777ance.github.io/localDNS/provenance.html>). The short form, which is
binding here:

- **Tiers:** `M` measured (a figure this stack produced, with its command) · `O` observed
  (read off the live box) · `D` derived (no higher than its weakest input) · `R`
  reconstructed (rebuilt from a *description* of the thing) · `A` asserted (intent, plan,
  lore). **Untagged reads as `R`.**
- **Transmission never promotes.** Copying, quoting, reformatting, publishing, and
  agreeing all preserve or lower a tier; only fresh contact with the origin raises it.
  Agreement is not provenance — five sources sharing an ancestor are one source (§G's
  collapsed jury, generalized). Age is not verification: an `R` file does not ripen into
  an `O` file in git, and a stale `O` means *re-observe, don't re-label*.
- **Gates (minimum tier to cross):** deploy to the box → `O`; print on a Statement → `M`;
  write into the seed/briefing as fact → `O` or label the tier; certify a jury verdict →
  measured `p̂`. These are the Bifrost `*()` release conditions (§H) — provenance is what
  goes inside the parentheses.
- **Mark it, don't remember it:** `provenance: TIER · source · date · verify: …` in the
  file's own comment syntax; `R`/`A` must carry the `verify:` route back to an origin.
  `python3 tools/check-provenance.py` enforces it (see § C).

**Deploy & git hygiene** — the summary; full procedure in
[docs/DEPLOY-PROTOCOL.md](docs/DEPLOY-PROTOCOL.md):

- **Box is the source of truth** — diff before overwrite; reconcile drift back into the repo first.
- **Verify the *effect*, not the command** — a failed `cp` + a clean restart silently reloads the old file; check `ss`/`dig` after every reload.
- **Validate before reload, back up before overwrite** — `unbound-checkconf` (etc.) first; a timestamped copy makes rollback one command.
- **git pull ≠ deploy** — it moves checkout files only; the running system is untouched until you apply a change (staged backlog: [docs/DEPLOY-QUEUE.md](docs/DEPLOY-QUEUE.md)).
- **Push:** always `git push -u origin Yggdrasil` — never to `main`, which moves only through an approved PR. Fast-forward when the branch is just `Yggdrasil` + your commits; retry with backoff; `tools/check-docs.py` green before committing docs, and `tools/check-doctrine.py` green before committing anything under `ai-orchestration/` or §G.

**Know which boundaries actually refuse** — the proxy register, `docs/architecture/proxies.md`
(adopted 2026-08-08). A proxy is anything that sits in a path, sees what crosses it, and can
refuse it: the agent git proxy, `$HTTPS_PROXY`, `gate.sh`, UFW, WireGuard, Pi-hole, the sops
vault, the LLM router. It is the strongest form of a site — a run cannot ignore it by not
reading it. Three rules bind here: **scope by reversibility, not by verb** (the agent proxy
blocks `--delete` but permits `--force`, and both orphan commits — so the force-push guard in
`gate.sh` is the site for that effect); **a refusal must be legible**, or a control becomes a
debugging expense; and **never write a declared boundary in the language of an enforced one** —
Bifrost's `@`/`#` mount table is honoured by a compliant run and by nothing else, which is fine
until it is taught as a guarantee. Register a new intermediary before relying on it.

**Never use the PR "watch" feature** — founder's standing instruction (2026-08-03).
Do not subscribe to PR activity (no `subscribe_pr_activity`), and don't offer to watch,
monitor, babysit, or autofix a PR — it's too expensive. When a PR is up, say so and
stop; the founder drives it from there.

**Conform to the LLM sampling doctrine** ([section G](#g-llm-sampling-doctrine--the-jury)) —
and when you *add* to it, **site the clause** where the run that could break it will read it
(§G's "Where these clauses live"): a command/agent file for judgment clauses, a static check
for mechanical ones. A clause that exists only in this briefing governs nothing.
Any work that configures, prompts, or aggregates this stack's own models — router
configs, orchestration, evals, agents — follows the doctrine by default: lazy anchor
→ governed-warm body → concurrent vote, with the invariants (match temperature with
governance; temperature is a variance dial, not an intelligence dial; measure `p`,
don't guess). Don't consume a single warm draw where a verdict matters — route it
through the Jury (`04-user-services/ai-orchestration/jury/`). Deviate only with a
stated reason.

---

## 4. Further reading

- **README.md** — top-level map + links to the interactive field guide (setup wizard)
- **docs/edda.html** — **The Edda**: the localDNS handbook — a self-contained,
  keyboard-first (⌘K command palette, `/`, `j`/`k`, `?`) single-page reference over the
  whole stack. Companion to the High Seat console (Hlidskjalf): the seat sees every
  realm, the Edda codifies them. No external deps — open it in any browser. Faithful to
  this briefing; when it disagrees with the live box, the box wins.
- **docs/DEPLOY-PROTOCOL.md** — the **how** of deploying: the repeatable per-change procedure for landing one committed change on the live t630 safely (sync the checkout → diff → back up → validate → reload → verify the *effect*). Read it before `cp`-ing anything onto the box. Linked from README; the DEPLOY-QUEUE stages assume it.
- **docs/DEPLOY-QUEUE.md** — the **what** of deploying: staging runbook of everything reconstructed/fixed in the repo but not yet on the live t630, in dependency order with copy-paste commands + per-stage verification. Work it once SSH to `192.168.1.118` is available. Linked from README.
- **docs/architecture/clear-refeed-protocol.md** — the sync → clear → refeed ritual: how to wipe a stale session and re-seed the latest CLAUDE.md losslessly. With the `SessionStart` hook (`.claude/hooks/refeed.sh`) installed, bare `/clear` runs the whole thing end-to-end (fires the §G lazy anchor first, then loads the seed); the `.claude/commands/reseed.md` slash command (`/reseed`) handles the no-clear refresh — it pulls the current seed `--ff-only` on **the branch you are on** (normally `Yggdrasil`, never `main`) before regenerating, so it never rebuilds a stale world and never pulls the older vetted tier over newer doctrine. **The seed** = the four-file briefing set (CLAUDE.md + README + `docs/ai-cto/context.md` + `docs/architecture/network-context.md`).
- **docs/architecture/INSTALL-NOTES.md** — fresh install simulation: every known break point and fix
- **docs/architecture/SKILLS.md** — skills demonstrated by the stack, each mapped to proving artifacts
- **PLUGINS.md** — which Claude Code Directory plugins apply to this config repo (short
  answer: none of the business ones — keep it lean)
- **docs/architecture/network-context.md** — design rationale: Docker networking, UFW/WireGuard
  forwarding, CAKE bufferbloat scope, Uptime Kuma monitor stack
- **docs/architecture/cell-grammar.md** — supporting architecture notes
- **docs/architecture/norns.md** — **three sessions, one branch, one eye.** Concurrent sessions now weave `Yggdrasil` at once. The eye is the branch tip: one session holds it (`fetch`), adds, and hands it back (`push`); a non-fast-forward rejection is the eye being handed back before you finished looking, not an error. Never `--force` — that does not pass the eye, it puts out the other Norn's. Carries the three lanes (**Urðr** the record · **Verðandi** work in flight · **Skuld** the debt), the claims table you append to **before** starting substantial work, and the failure mode that git cannot catch: **duplicate assignment**. Sessions cannot message each other — `ListAgents` is empty and the CCR server exposes `create_session` with no `send_message` — so the repo is the only channel, and a claim is a commit. Read §4 and `git log origin/Yggdrasil` before spawning another Norn or starting a large piece of work.
- **docs/architecture/proxies.md** — **Heimdall: the proxy register.** Every intermediary that stands in a path and can refuse what crosses it — the agent git proxy, the egress proxy, `gate.sh`, UFW, WireGuard, Pi-hole, Unbound, the vault, the LLM router, ttyd — with seven questions answered for each (what it mediates, who holds the authority, what it can refuse, whether refusal is legible, bypassable, fail-open/closed, and **scoped by verb or by effect**). It separates **enforced** (an intermediary refuses) from **declared** (the caller is asked to comply) from **ambient** (in the path, refuses nothing) — because a declared boundary written in the language of an enforced one buys the confidence of a control without the behaviour of one, and this repo had three of those. Proxy-scoping is the rung **above** `warrant-sites.md`'s ladder: a check sits in a run's given-set and is bypassed by a run that never invokes it, while a proxy sits in the run's world. Read it before adding any intermediary, and before trusting one you did not verify. Law 1 is the one that bit us: **scope by reversibility, not by verb** — the agent proxy blocks `--delete` and permits `--force`, which orphans commits just as well.
- **docs/architecture/warrant-sites.md** — **where an invariant has to live to bind anything**: a run's warrant configuration (given-set · check obligation · confidence policy), why briefing prose and citations are not sites, the ranked site ladder, and the audit of which invariants in this repo are actually sited versus merely stated. Read it before writing a new rule anywhere.
- **docs/provenance.html** — **the Provenance Ladder**: how a claim earns authority here (`M`/`O`/`D`/`R`/`A`), why transmission never promotes a tier, the four gates that check one before anything irreversible, the tag grammar, and the laundering catalogue. Published at <https://a777ance.github.io/localDNS/provenance.html>. Read it before citing a reconstructed config as fact or a plurality as a verdict — enforced by `tools/check-provenance.py`.
- **tools/check-docs.py** — validates Markdown links (anchors + file links) AND inline repo-path references across **every** doc in the repo, and hard-fails on any stale legacy 1.x folder path (the pre-consolidation `01-unbound`, `12-secrets`, … names used with a trailing slash). Run before committing. Intentionally-absent paths (e.g. the un-snapshotted `langgraph-router/`) are allowlisted in the script. It also enforces one cross-file invariant: the **Bifrost sweep string** (the fixed string a bare `'` returns, §H) must be **byte-identical** across all three surfaces carrying it — CLAUDE.md is canonical. The **expansion template** (what a bare `` `seed` `` fills in) is held to the same standard and one more: byte-identical across the same three surfaces, *and* it must reduce to the sweep once its `(fill in)` slots and whitespace are struck — the derived clause that stops three agreeing copies of a *wrong* skeleton. A deterministic answer is only as good as the agreement of its sources. It also enforces the companion invariant: the **glyph roles** must match across spec §1, the rendered page, and §H. The sweep proves the surfaces agree on the glyphs' *order*; this proves they agree on what the glyphs *mean* — the half that actually decided wrong, when `@` read "signage" on the page for a full pass after the spec had reassigned it to "source". Deliberately narrow: it compares the first word of each archetype, so a role **reassignment** fails while the presentational differences the surfaces are entitled to ("Sanity / Tollbooth" vs "Sanity") pass. A check that failed on phrasing would be switched off, and an off check is worse than a narrow one.
- **tools/sync-briefings.py** + **`04-user-services/ai-orchestration/briefing-block.md`** — **the parallel-session check.** Bifrost is active in every repo, so a dozen `CLAUDE.md` files carry the schema and are required to agree — but git only conflicts on the *same* file, and these are *different* files with an agreement obligation. Two sessions can each run green, each push cleanly, and still leave the portfolio self-contradictory; that is exactly how nine briefings kept describing a schema without `'` after Ignition landed here. So the copies stop being copies: `briefing-block.md` is canonical, the script renders it, and the gate blocks a commit that would ship drift. Rendered blocks are build output — **never hand-edit them.** Siblings not checked out are skipped and named, so green never silently means "checked nothing." The script carries a **registry** of canonical blocks, not one hardcoded block: `branch-policy-block.md` (§3's `Yggdrasil` / Well-of-Mimir rule) rides the same machinery, because it failed the same way in the more dangerous direction — not drifting, but **missing** from eight of ten briefings, where silence assigned "cut a new branch" 337 times. A narrow tripwire also fails any briefing still carrying the retired **"Push to `main`, no branches"** directive, so the supersession cannot be half-applied.
- **tools/check-branch-cap.py** + **tools/retire-stale-branches.sh** — **the branch cap and the one-time cleanup it followed.** The branch-per-session habit produced **338** stale `claude/*` refs across ten repos; **226 held commits that existed nowhere else**, so bulk deletion would have destroyed work. The repair was to make deletion *provably* lossless first: one octopus commit per repo whose parents are every stale tip, pushed as **`doom-drawer/2026-08-08`** — "Didn't Organize, Only Moved", the ADHD filing trick applied to refs — after which every orphaned commit stays reachable from a single ref. The name states the honest limit: the drawer is *findable*, not *sorted*, and that is deliberate, because sorting is the step at which things get thrown away. `retire-stale-branches.sh` then deletes the 338 and the superseded `archive/*` label (run it by hand — deletion returns HTTP 403 from the agent environment, so a session cannot do it; the drawer itself is kept). `check-branch-cap.py` is the site that stops the habit returning: over 9 branches fails at the commit gate, except for refs already in a drawer, which report as PENDING so the cap can be enforced before the cleanup has run. Open the drawer with `git log --oneline doom-drawer/* --not origin/Yggdrasil`; take something back out with `git branch <name> <sha>`.
- **tools/check-doctrine.py** — asserts the **mechanically-decidable** clauses of §G against the code that implements them: the juror sampler's `temperature`/`top_p`/`top_k`/`max_tokens` defaults, the CLI defaults (the real entry point), and that the penalties are **actually sent** rather than inherited from a vendor default. Deliberately narrow — the posture clauses (lazy anchor, vote-as-governor, measure `p̂`) don't decide mechanically and are sited in `.claude/commands/` and `.claude/agents/juror.md` instead, so a green run is **not** a claim the doctrine was followed, only that the numbers still agree.

---

## 5. AI CTO state

Read `docs/ai-cto/context.md` in this repo for current open items and component status.
Its **"Default next actions"** block at the top is the pre-computed session-start
queue — the ordered default next moves (P1 ship chain + repo-hygiene) so a fresh
session doesn't re-derive them. Start there when the founder hasn't named a priority.
The portfolio hub (cross-repo roadmap, decisions log, tech debt) lives in
`DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.
