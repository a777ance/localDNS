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

| Repo path | System path | Reload |
| --------- | ----------- | ------ |
| `01-core-network/unbound/server.conf` | `/etc/unbound/unbound.conf.d/server.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/tuning.conf` | `/etc/unbound/unbound.conf.d/tuning.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/remote-control.conf` | `/etc/unbound/unbound.conf.d/remote-control.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/root-auto-trust-anchor-file.conf` | `/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/streaming-forward.conf` | `/etc/unbound/unbound.conf.d/streaming-forward.conf` | `sudo systemctl restart unbound` |
| `01-core-network/unbound/unbound-cache-dump` | `/usr/local/bin/unbound-cache-dump` | — |
| `01-core-network/unbound/unbound-cache-load` | `/usr/local/bin/unbound-cache-load` | — |
| `01-core-network/unbound/unbound-cache-dump.service` | `/etc/systemd/system/unbound-cache-dump.service` | `sudo systemctl daemon-reload` |
| `01-core-network/unbound/unbound-cache-dump.timer` | `/etc/systemd/system/unbound-cache-dump.timer` | `sudo systemctl daemon-reload` |
| `01-core-network/unbound/unbound.service.d/override.conf` | `/etc/systemd/system/unbound.service.d/override.conf` | `sudo systemctl daemon-reload` |
| `01-core-network/pihole/docker-compose.yml` | `~/pihole/docker-compose.yml` | `cd ~/pihole && docker compose up -d` |
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
| `04-user-services/ai-orchestration/jury/jury.py` | run on the t630 (or any host with the key) — adaptive self-consistency voter for Kimi K3 (see section G) | `python3 jury.py deliberate …` / `… calibrate …` |
| `04-user-services/ai-orchestration/jury/.env.example` | copy to `…/jury/.env` (git-ignored), add `FIREWORKS_API_KEY` | — |
| `docs/statements/tools/collect/nftables-accounting.nft` | load with `sudo nft -f nftables-accounting.nft` | re-run anytime (idempotent) |
| `docs/statements/tools/collect/populate_sets.py` | `~/a777ance/collect/populate_sets.py` (+ cron `3 */6 * * *`) | `crontab -e` |
| `docs/statements/tools/collect/collect_stats.py` | `~/a777ance/collect/collect_stats.py` (+ cron `30 0 * * *`) | `crontab -e` |
| `tools/check-docs.py` | run directly (validate Markdown links across root docs) | `python3 tools/check-docs.py` |
| `tools/migrate.sh` | one-time 1.x→2.0 folder migration (already applied) | — |

**Drift to reconcile — documented for the live box but NOT in this repo snapshot.**
The README 2.0 architecture diagram lists these under `04-user-services/`, and the
sections below still describe their live behavior, but no config is checked in. Either
snapshot the config here (so the repo stays a valid rollback target) or trim the
reference:

| Missing from repo | What it should hold | Referenced in |
| ----------------- | ------------------- | ------------- |
| `04-user-services/console/` | High-seat launcher `index.html`, `console.service`, `ttyd-thinclient.service`, `ttyd-laptop.service`, `ttyd.env.example`, `browser-odin.md` | topology services table, Known issues |
| `04-user-services/ai-orchestration/` | LiteLLM `docker-compose.yml`, `config.yaml`, `.env.example`, `langgraph-router/` (Odin supervisor) — still missing. **`jury/` (adaptive self-consistency voter) now snapshotted here** — see section G. | topology services table, Known issues |
| secrets vault (was `12-secrets/`) | sops+age `vault/*.env.sops`, `.sops.yaml`, `secrets.manifest`, `seal.sh`/`unseal.sh`/`rotate-secrets.sh` | Known issues (pihole/router/ttyd secrets) |
| `01-core-network/unbound/local-records.conf` | LAN-only A records (`ai`/`chat`/`console`/`term`/`laptop`/`kuma`/`pihole`.home.lan → t630) | Unbound config section |

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

**Five** drop-ins live in `01-core-network/unbound/` in this repo, loaded
alphabetically (A→Z) by Unbound from `/etc/unbound/unbound.conf.d/` — listed Z→A
here per house style:

| File | Purpose |
| ---- | ------- |
| `tuning.conf` | All performance and cache values — single source of truth |
| `streaming-forward.conf` | Forward-zones: streaming/media domains → Cloudflare over DoT (`1.1.1.1@853`, `forward-tls-upstream`); all else recursive. Sets `tls-cert-bundle` for upstream cert validation. |
| `server.conf` | Interface, port, access-control, security flags |
| `root-auto-trust-anchor-file.conf` | DNSSEC root trust anchor |
| `remote-control.conf` | Unix socket for `unbound-control` |

A sixth drop-in, `local-records.conf` (LAN-only A records: `ai`/`chat`/`console`/`term`/`laptop`/`kuma`/`pihole`.home.lan → the t630, so the console sidebar pins names not IP:ports; `local-zone … transparent` overrides only the names defined, not the whole zone), is **documented but not present in this repo** — see the "drift to reconcile" note in section C. Add it under `01-core-network/unbound/` to make the LAN names reproducible from the repo.

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

**The tool.** `04-user-services/ai-orchestration/jury/` implements this end to end —
an adaptive sequential voter that empanels jurors in concurrent batches and stops on
a Dirichlet posterior (easy prompts settle at `--min-n`, split ones run to
`--max-n`), plus a `calibrate` mode that measures `p̂` and separates dispersed-error
tasks (voting works, even below `p=0.5`) from systematic bias (voting entrenches the
wrong answer). Standard library only, offline `--mock` mode for keyless testing. See
its README.

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
| WireGuard peers 10.8.0.4, 10.8.0.5, 10.8.0.6 | Now reconciled into `01-core-network/wireguard/wg0.conf` (real public keys) but still UNIDENTIFIED with no recent handshake — identify each device or remove the stale peer. |
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

Every commit to `main` must leave README.md able to reproduce a working system on
clean Ubuntu 24.04.

**Push to `main`, no branches** — founder's standing instruction (2026-06-05). Don't
open PRs or park work on feature branches for these repos; land each change as a
coherent, deployable commit straight on `main`.

**Conform to the LLM sampling doctrine** ([section G](#g-llm-sampling-doctrine--the-jury)).
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
- **docs/architecture/clear-refeed-protocol.md** — the sync → clear → `/refeed` ritual: how to wipe a stale session and re-seed the latest CLAUDE.md losslessly. With the `SessionStart` hook (`.claude/hooks/refeed.sh`) installed, bare `/clear` runs the whole thing end-to-end; the `.claude/commands/refeed.md` slash command handles the no-clear refresh.
- **docs/architecture/INSTALL-NOTES.md** — fresh install simulation: every known break point and fix
- **docs/architecture/SKILLS.md** — skills demonstrated by the stack, each mapped to proving artifacts
- **PLUGINS.md** — which Claude Code Directory plugins apply to this config repo (short
  answer: none of the business ones — keep it lean)
- **docs/architecture/network-context.md** — design rationale: Docker networking, UFW/WireGuard
  forwarding, CAKE bufferbloat scope, Uptime Kuma monitor stack
- **docs/architecture/cell-grammar.md** — supporting architecture notes
- **tools/check-docs.py** — validates every Markdown link in the root docs (run before committing)

---

## 5. AI CTO state

Read `docs/ai-cto/context.md` in this repo for current open items and component status.
The portfolio hub (cross-repo roadmap, decisions log, tech debt) lives in
`DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/portfolio.md`.
