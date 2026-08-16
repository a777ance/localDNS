<!-- provenance: D · Codex audit of this repo (2026-08-09) + the first live drift audit against the t630 (2026-08-09) + this session's fixes · 2026-08-09 -->

# Remediation Board — the standing track rotation

Six tracks that close the gap between "well-documented" and "operationally closed."
Adopted 2026-08-09 from an outside audit of this repo, extended with what the first
live drift audit actually found.

**Why this file exists.** The board was agreed in a session, and a plan that lives only
in a session transcript has an author and no **site** — the next session's given-set
omits it, so it governs nothing (`docs/architecture/warrant-sites.md`). This is the site.
The session-start queue in `docs/ai-cto/context.md` points here; when a track's state
changes, change it **here**, in the same commit as the work.

**The thesis the board serves:** *stop expanding the canopy; finish the trunk.* The
appliance's promise is "this box protects and explains your home network." Until it can
produce one honest, measured, client-ready Statement, everything above that — AI
orchestration, console surfaces, operator portfolios — is optional scaffolding.

---

## How to work this board

Each session, take the **first unblocked item** in this order. Skip any track the
founder doesn't want that day and cycle to the next; this is a rotation, not a queue.

1. **SSH to the t630 available** → Track 1 (drift) and Track 4 (exposure verification).
2. **No SSH, repo work possible** → improve checks, docs, and scripts so the next live
   session is nearly mechanical.
3. **Measurement layer ready** → Track 3, then confirm Statements no longer read sample
   category data.
4. **Product validation ready** → Track 5.
5. **Core closed** → Track 6.

**Two standing rules that outrank the rotation.** The live t630 is the source of truth —
reconcile drift *into* the repo before deploying over it (`docs/DEPLOY-PROTOCOL.md`).
And never print a figure the box did not measure; omit the section instead.

---

## Status at a glance

| # | Track | State | Blocked by |
| - | ----- | ----- | ---------- |
| 1 | Repo/live drift closure | **In progress** — first audit run 2026-08-09 | — |
| 2 | Snapshot live-only assets | Not started | needs the box |
| 3 | Measured data plumbing | **Cleared to deploy** | — |
| 4 | Security & exposure verification | **Open — one urgent item** | — |
| 5 | First real measured Statement | Blocked | Track 3 · Kuma API key |
| 6 | AI/console platform hardening | Deferred by design — **exception:** GPU-rental tier (2026-08-16) | Tracks 3–5 |

---

## Contents (reverse-block order)

- [Track 6 — AI/console platform hardening](#track-6--aiconsole-platform-hardening)
- [Track 5 — First real measured Statement](#track-5--first-real-measured-statement)
- [Track 4 — Security and exposure verification](#track-4--security-and-exposure-verification)
- [Track 3 — Measured data plumbing](#track-3--measured-data-plumbing)
- [Track 2 — Snapshot live-only assets](#track-2--snapshot-live-only-assets)
- [Track 1 — Repo/live drift closure](#track-1--repolive-drift-closure)
- [Where this came from — the audit findings](#where-this-came-from--the-audit-findings)
- [Session log](#session-log)

Per house style the blocks read newest-first (Track 6 at the top, Track 1 at the
bottom), but **the numbers are authoritative** — they encode priority and dependency.
Follow the numbers, not the page order, and never renumber.

---

## Track 6 — AI/console platform hardening

**Goal:** keep advanced operator tooling useful without letting it outrun the base
appliance.

> **Exception (2026-08-16, founder-approved).** The `cloud-gpu-reason` tier in
> `04-user-services/ai-orchestration/config.yaml` — a rented GPU pod reached over
> Tailscale — moves ahead of Tracks 3–5, a deliberate carve-out from this track's
> deferral. Scope is narrow: pick a provider (RunPod, chosen over Lightning AI
> Studios for this because the design wants a persistent Ollama endpoint reachable
> by hostname, not a notebook session — see `04-user-services/ai-orchestration/README.md`
> "Offload heavy reasoning to a rented GPU"), pin the pod's Tailscale host in
> `config.yaml`, and land an idle-stop safety net so a forgotten pod doesn't drain the
> prepaid balance. **Everything else in this track — the console/ttyd hardening and the
> Odin supervisor deploy — still waits on Tracks 3–5**, per the checklist below.

- [ ] Verify the LiteLLM router and Open WebUI are deployed and reachable.
- [ ] Verify the console launcher ("high seat") and both ttyd terminals.
- [ ] Define the web-shell posture explicitly: auth model, lockout/rate-limiting, TLS
      (`ttyd -S`), session logging + retention, no default credentials.
- [ ] Deploy the Odin supervisor **only after** the gateway is stable.

> **Open question raised by the 2026-08-09 drift audit.** `CLAUDE.md`'s topology table
> lists console (8088), ttyd (7681/7682) and the LLM router (4040/3000) as **live
> services**, but none of their config files were found at the documented paths on the
> box. Either the audit's path list is wrong or the briefing overstates the live system.
> **Resolve this before anything else in this track** — it is a bigger finding than any
> single diff, and it decides whether the briefing itself needs correcting.

---

## Track 5 — First real measured Statement

**Goal:** one client-grade artifact built from real box measurements.

- [ ] Build from real Pi-hole / Uptime Kuma / WireGuard / nftables data.
- [ ] **Omit** unsupported sections rather than inventing them — the "How You Compare"
      neighbour benchmark has no cohort, and by-category volume is only real once
      Track 3 lands.
- [ ] Test the Statement PWA install on iOS and Android.
- [ ] Generate one household Statement.
- [ ] Document the repeatable monthly process.

**Hard dependency:** the Uptime Kuma API key (Track 3). Without it `uptime` and
`latency_ms` are `null`, and those are two of the four figures a Statement prints.

---

## Track 4 — Security and exposure verification

**Goal:** prove the box exposes only what it should. Re-run after **every**
deploy-affecting change; this track never closes.

- [ ] **URGENT — rotate the Pi-hole admin/API credential.** The live
      `~/pihole/docker-compose.yml` carries it hardcoded in cleartext, in a file that is
      not root-owned, and the 2026-08-09 drift audit copied it to a laptop in the clear.
      Treat it as burned: set `PIHOLE_WEBPASSWORD` in `~/pihole/.env`, deploy the
      repo's env-sourced compose (`01-core-network/pihole/docker-compose.yml`,
      DEPLOY-QUEUE Stage 4), restart, and destroy the local audit copy.
- [ ] **URGENT — disk pressure on the eMMC.** FTL reported `92% is used (12.9GB used,
      13.9GB total)` on 2026-08-09, i.e. ~1GB free on the 16GB eMMC. This is an
      availability *and* an honesty risk: when the disk fills, FTL stops writing its
      long-term DB, and the query counts a Statement is built from silently stop being
      complete — the failure looks like a quiet month, not an outage. Diagnose
      (`docker system df`, `du -xh`, FTL DB size, journal size), reclaim, then decide a
      standing retention policy. Note the nightly collector writes to `/var/lib/a777ance`
      and `/var/log/a777ance` on the same filesystem.
- [ ] Verify WAN reaches **only** WireGuard (51820/udp).
- [ ] Verify console + ttyd are LAN + WG only, never port-forwarded.
- [ ] Verify the Pi-hole UI is not WAN-exposed.
- [ ] Verify DNS answers for both LAN and WireGuard clients.
- [ ] Verify no sensitive domains sit on the Cloudflare forward path.
- [ ] Verify no secrets are in git.

---

## Track 3 — Measured data plumbing

**Goal:** unlock real, honest Network Activity Statements. This is the highest-value
product unlock on the board.

- [x] Fix double-counting — a category hit now `return`s instead of also falling through
      into `c_other` (`docs/statements/tools/collect/nftables-accounting.nft`).
- [x] Build the deploy fast path (`tools/deploy-volume-layer.sh`).
- [x] Install cron in **root's** crontab with logging to `/var/log/a777ance/` — every
      source the jobs read is root-only, so a login-user install fails silently while the
      counters decay behind a still-measured-looking Statement (CLAUDE.md § F).
- [x] Plumb the Uptime Kuma API key through `/etc/a777ance/collect.env`.
- [ ] **Run the deploy.** Cleared: it touches only `docs/statements/tools/collect/`, a new
      `inet a777acct` table, and root's crontab — no drifted file is in its path.
- [ ] Mint the Kuma API key (*Settings → API Keys*) and fill in `KUMA_KEY`.
- [ ] Confirm `volume.by_category` is populated and non-zero after one refresh cycle.
- [ ] Check `/var/log/a777ance/` after the first scheduled run — silence there is the
      only early warning that a job is failing.

---

## Track 2 — Snapshot live-only assets

**Goal:** stop important system state from living only on the box. While these are
missing, the repo is a partial memory, not a recovery artifact.

- [ ] Snapshot the Odin supervisor from the live box —
      `04-user-services/ai-orchestration/langgraph-router/`. **Snapshot it, don't
      fabricate it from lore.**
- [ ] Snapshot the orchestration blueprint.
- [ ] Seal the real secrets into the `vault/` directory as `*.env.sops` (needs an age key
      plus real values; the tooling is already checked in).
- [ ] Retire the missing-asset allowances in `tools/check-docs.py` once each lands.

---

## Track 1 — Repo/live drift closure

**Goal:** make the repo trustworthy as the rollback target.

- [x] Build the read-only drift audit (`tools/t630-drift-audit.sh`).
- [x] Fix the sudo TTY-scoping bug that made every root-owned file report unreadable.
- [x] First live audit run (2026-08-09): 2 match · 3 comment-only · 2 repo-ahead ·
      1 real defect · 7 absent.
- [x] Reconcile `cap_add: SYS_NICE` back from the box into the repo.
- [ ] **Fix the audit's core blind spot:** it reports one `differs` and cannot separate
      *the box has something the repo lost* (reconcile backward) from *the repo has
      something the box has not received* (a staged deploy). Those demand opposite
      actions, and two of five diffs were the second kind.
- [ ] **Fix the audit's secret leak:** it copies live files verbatim to the operator's
      laptop, credentials included. Redact or refuse known-secret-bearing paths.
- [ ] Resolve the 7 `absent on box` rows — see the open question in Track 6.
- [x] Decide the `dnsmasq_data:/etc/dnsmasq.d` mount. **Resolved 2026-08-09:** deployed
      and observed — the directory is empty inside the container and DNS resolves
      normally, so it masks nothing (v6 really did move config into `pihole.toml`).
      Harmless but useless, and it makes FTL emit a duplicate disk-shortage warning for
      that mount. Recommend dropping the line; not a risk either way.
- [ ] Remove stale "reconstructed — verify against the box" warnings once each file is
      confirmed, so the remaining warnings keep meaning something.

---

## Where this came from — the audit findings

The seven exposures the tracks exist to close:

1. **The repo is not a complete rollback target** — Odin and the sealed vault files live
   only on the box. → Track 2
2. **Too much is reconstructed, not verified** — rebuilt from documentation rather than
   read off the box. → Track 1
3. **The product milestone is blocked by measurement, not UI** — the answer is data
   plumbing, not more front-end polish. → Track 3
4. **Scope-pressure risk** — the canopy is outrunning the trunk. → Track 6 deferral
5. **The deploy order is cognitively inverted** for outside operators — reverse-block
   presentation against execute-by-stage-number. Fine for the founder and for agents
   trained on the house style; reconsider if this becomes operator documentation.
6. **Pi-hole v6 config unverified** — `FTLCONF_webserver_port` and the v6 volume layout
   were reconstructed. → **Confirmed** by the 2026-08-09 audit.
7. **Web terminals are high-consequence** — browser-reachable shells raise the security
   bar. → Track 4 / Track 6

What was going **right** and should not be disturbed: the service-boundary repo layout;
Unbound (not Pi-hole) owning DNS policy; host networking for Pi-hole justified rather
than cargo-culted; the public/private data boundary; the honesty-of-the-kept-document
rule; a staged deploy queue instead of vague next steps; and a WireGuard-only WAN door.

---

## Session log

Newest first.

### 2026-08-16 — GPU-rental tier carved out of Track 6's deferral

- Founder approved wiring the `cloud-gpu-reason` tier (rented GPU pod over Tailscale)
  ahead of Tracks 3–5, as a deliberate exception — recorded here per RCPS so the next
  session doesn't re-litigate the ordering (Root Cause Problem Solving; Record ·
  Commit · Push · Sync — CLAUDE.md §3).
- Provider: RunPod, chosen over Lightning AI Studios because the config wants a
  long-lived Ollama endpoint reachable by hostname, not an interactive notebook
  session. Lightning AI Studios stays the recommended tool for a one-off test-drive
  of a big model; RunPod is for the real integration.
- Landed: RunPod named explicitly in `config.yaml` / `README.md` / `.env.example`
  comments, and a `runpod-idle-stop.sh` safety-net script (cron-driven) that stops
  the pod after a configurable idle window — the mechanical enforcement of "always
  hit stop," sited as a script rather than left as advice in a briefing.
- Still placeholder: `TAILSCALE_GPU_HOST` and the RunPod API key/pod ID — no real
  pod has been rented yet. Pin these once one exists (`docs/DEPLOY-QUEUE.md` Stage 8).

### 2026-08-09 — Pi-hole credential rotated; disk pressure found

- Rotated the Pi-hole credential onto `~/pihole/.env` (`0600`) and deployed the
  env-sourced compose (Stage 4). The rotation is proven by construction: the compose
  uses `${PIHOLE_WEBPASSWORD:?…}`, which fails closed, so the container could not have
  started without reading the file. DNS verified answering and blocking after restart.
- `cap_add: SYS_NICE` was still absent post-deploy — the operator's checkout predated
  the fix, so the pre-fix file was the one copied. FTL's own
  `CAP_SYS_NICE required` warning caught it. Pull, re-copy, re-up.
- **Found the eMMC at 92% full (~1GB free)** — not visible from any file in the repo;
  it surfaced only from FTL's startup log on a live restart. Now the urgent item in
  Track 4.
- FTL also warns `CAP_SYS_TIME required, NTP client not available` — low priority, but
  decide whether the compose should grant it or the briefing should say it is declined
  on purpose.

### 2026-08-09 — board adopted; Tracks 1 and 3 opened

- Landed the Track 1 + Track 3 fast-path helpers on `main` after the original commit was
  lost in transit between environments.
- Fixed two **silent** helper failures before first use: `sudo -n` TTY scoping (would
  have reported false catastrophic drift) and login-user cron with `/dev/null` output
  (would have let the nft sets age out while counters decayed behind a Statement that
  still looked measured).
- First live drift audit against the t630. Read: 3 of 5 diffs were comment-only; 2 were
  the repo deliberately ahead (staged Stages 2 and 4); 1 was a genuine repo defect.
- Reconciled `cap_add: SYS_NICE` from the box into the repo (`provenance: O`).
- Discovered from a live run — not from reading files — that Uptime Kuma's `/metrics` is
  authenticated and `--kuma-key` defaults to empty, so uptime and latency were never
  going to be measured. Plumbed through `/etc/a777ance/collect.env`.
- Found a hardcoded Pi-hole credential on the live box. Rotation is the urgent item in
  Track 4.
