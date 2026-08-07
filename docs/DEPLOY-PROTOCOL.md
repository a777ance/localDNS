# Deploy Protocol — landing one change on the live t630

The **repeatable procedure** for taking a single committed repo change and applying it
to the live box at `192.168.1.118`, safely, every time. This is the *how*;
[docs/DEPLOY-QUEUE.md](DEPLOY-QUEUE.md) is the *what* (the one-time backlog of everything
still staged for the box). Every stage in the queue assumes the procedure written here.

> **The live t630 is the source of truth.** This repo is a rollback target, not a
> master. A deploy therefore always **diffs the live file first** and reconciles any
> drift *back into the repo* before overwriting — never blindly stamps the repo over a
> working box.

**When this applies:** a config/unit/compose file that already has a row in the
[CLAUDE.md § C deploy table](../CLAUDE.md#c-deploy-paths) changed in the repo, and you
want it live. **When it doesn't:** a first-time bring-up (use the DEPLOY-QUEUE instead),
or a docs-only / scaffolding-only change (nothing to deploy).

---

## The five golden rules

These survive even if you skip a step — they are the failures this protocol exists to
prevent, each learned the hard way:

1. **Never `cp` from a stale tree.** Sync the box's checkout *before* you copy, and
   watch the copy's exit. A failed `cp` followed by a "successful" `systemctl restart`
   is a **silent no-op** — the service reloads the old file and reports healthy.
2. **The box wins — diff before you overwrite.** Reconcile any live-only content
   (hand-edits, real keys, box-specific values) back into the repo first. A deploy must
   never discard a working box's state.
3. **Validate before you reload; verify the *effect* after.** Check the config
   (`unbound-checkconf`, `docker compose config`, `nft -c`) before restarting, then
   confirm the change actually took at the running service — inspect the behavior
   (`ss`, `dig`, `ufw status`), not just that the restart command returned 0.
4. **Back up the live file before you touch it.** One timestamped copy makes rollback a
   single command. A half-deployed resolver is worse than the old one.
5. **Land on `main`, don't leave the box on a branch.** Repo convention is push-to-main
   (see CLAUDE.md § 3). Deploying an unmerged branch is the exception — merge it and put
   the box back on `main` immediately after.

---

## How to read this protocol

- **Execute in PHASE-NUMBER order — Phase 0 first, Phase 5 last.** Per house style the
  phases are presented newest-block-first (Phase 5 at the top, Phase 0 at the bottom),
  but the **numbers are authoritative**: they encode the true execution order. Follow
  the numbers, not the page order. The steps *within* each phase run forward.
- Every "deploy" path maps repo → system per the
  [CLAUDE.md § C deploy table](../CLAUDE.md#c-deploy-paths); every "verify" draws from
  [CLAUDE.md § 2](../CLAUDE.md#2-verification).
- Commands use `USER@192.168.1.118` and the box's checkout at `~/localDNS` — substitute
  your real login. Over WireGuard, `USER@10.8.0.1` reaches the same box.
- The [worked example](#worked-example--the-unbound-loopback-tighten) at the bottom runs
  every phase end-to-end on a real change.

## Contents (reverse-phase order)

- [Phase 5 — Record it, and roll back if you must](#phase-5--record-it-and-roll-back-if-you-must)
- [Phase 4 — Verify the effect, not that the command ran](#phase-4--verify-the-effect-not-that-the-command-ran)
- [Phase 3 — Back up, deploy, then validate before reload](#phase-3--back-up-deploy-then-validate-before-reload)
- [Phase 2 — Diff before you overwrite](#phase-2--diff-before-you-overwrite)
- [Phase 1 — Sync the box's checkout](#phase-1--sync-the-boxs-checkout)
- [Phase 0 — Preflight in the repo](#phase-0--preflight-in-the-repo)
- [Worked example — the Unbound loopback tighten](#worked-example--the-unbound-loopback-tighten)

---

## Phase 5 — Record it, and roll back if you must

Close the loop so the repo knows the box matches — and keep the escape hatch ready.

1. **Record the deploy.** Tick the matching item in
   [docs/DEPLOY-QUEUE.md](DEPLOY-QUEUE.md) and/or flip the row in
   `docs/ai-cto/context.md` from "not deployed" to "Running", with the date and
   "verified". If nothing tracks this file yet, that's fine — the point is that a future
   session can tell the box matches the repo.
2. **Put the box back on `main`** if you deployed an unmerged branch (golden rule 5):
   ```bash
   git -C ~/localDNS checkout main && git -C ~/localDNS pull --ff-only origin main
   ```
3. **Rollback (reference)** — if Phase 4 failed, or the change misbehaves later. Restore
   the timestamped backup from Phase 3 and reload:
   ```bash
   sudo cp /etc/unbound/unbound.conf.d/server.conf.bak-<ts> \
           /etc/unbound/unbound.conf.d/server.conf
   sudo unbound-checkconf && sudo systemctl restart unbound
   ```
   …or revert from the repo and redeploy the previous version:
   ```bash
   git -C ~/localDNS checkout HEAD~1 -- 01-core-network/unbound/server.conf
   # then re-run Phase 3 with the reverted file
   ```

## Phase 4 — Verify the effect, not that the command ran

The trap this phase closes: a `systemctl restart` that "succeeded" while the file it
reloaded never changed (because Phase 3's `cp` had failed). Prove the new state, don't
assume it.

1. **Confirm the change took at the running service** — inspect behavior, not exit codes:
   ```bash
   sudo ss -ulnp | grep 5335      # shows the NEW state (e.g. 127.0.0.1:5335), not just "up"
   ```
2. **Run the [CLAUDE.md § 2](../CLAUDE.md#2-verification) lines for the touched service.**
   For a DNS change: DNSSEC `ad` flag present, both resolution paths resolve, and the
   Pi-hole → Unbound path still answers:
   ```bash
   dig @127.0.0.1 -p 5335 example.com +dnssec +short
   docker exec pihole dig @127.0.0.1 -p 5335 example.com +short
   ```
3. **If any check fails, roll back now** (Phase 5, step 3) — don't leave a half-applied
   service running. Then fix in the repo and start over.

**The cleavage test — for anything that wraps a payload.** The steps above prove a
mechanism is *up*. For a wrapper — WireGuard, DoT, any tunnel or proxy — that is not the
same as proving the payload arrived usable. A wrapper that crosses but is never unwrapped
by something able to act on the contents is an unopened box counted as a delivery, and it
reports green on every check you were running. This stack has already been bitten by it
twice: VPN peers whose tunnel came up cleanly while their DNS never reached Pi-hole
(Docker DNAT sat in the path for queries sourced from `wg0`), and the `::/0` IPv6 black
hole (handshake succeeds, pages hang).

So: **name the thing that unwraps it, and test from the far side.** `sudo wg show` proves
the tunnel exists; it proves nothing about what came out of it.

```bash
# From a peer, not from the box — proves the tunnel's DNS is actually filtered:
dig @10.8.0.1 <a-domain-you-know-is-blocked> +short    # expect the block, not an answer
dig @10.8.0.1 example.com +short                        # expect normal resolution
curl -s https://ifconfig.me                             # expect the home WAN IP, not the peer's ISP
```

The general form: *what would this look like if the wrapper arrived and nothing opened
it?* — then check for exactly that. Background:
[`microbiology/amphiphiles.md`](architecture/microbiology/amphiphiles.md) §2.

## Phase 3 — Back up, deploy, then validate before reload

1. **Back up the live file, timestamped** (golden rule 4) — this is your one-command
   rollback:
   ```bash
   sudo cp /etc/unbound/unbound.conf.d/server.conf{,.bak-$(date +%Y%m%d-%H%M%S)}
   ```
2. **Copy repo → system** per the § C row. Use `install` when ownership/mode matter
   (secrets are `-m 600`, e.g. `/etc/a777ance/ttyd.env`):
   ```bash
   sudo cp ~/localDNS/01-core-network/unbound/server.conf \
           /etc/unbound/unbound.conf.d/server.conf
   ```
   **Watch this command's output.** `cp: cannot stat …` means *nothing deployed* — stop,
   fix the path (usually Phase 1 wasn't done), and do not continue to the reload.
3. **Validate the config *before* reloading**, wherever the service can:
   ```bash
   sudo unbound-checkconf            # Unbound
   # docker compose config           # compose files
   # sudo nft -c -f <file>           # nftables rulesets
   # sudo ufw --dry-run <rule>       # firewall rules
   ```
4. **Reload with the exact command from the § C table** — do not guess it:
   ```bash
   sudo systemctl restart unbound
   ```

## Phase 2 — Diff before you overwrite

The box is the source of truth (golden rule 2). Find out what you're about to replace
*before* you replace it.

1. **Diff live vs repo for each changed file** (map system ← repo via § C):
   ```bash
   diff /etc/unbound/unbound.conf.d/server.conf \
        ~/localDNS/01-core-network/unbound/server.conf
   ```
2. **If the live file carries content the repo doesn't** — hand-edits, real keys,
   box-specific values, a comment someone fixed on the box — **reconcile it back into the
   repo first**: pull that content into the repo file, commit + push, then re-sync
   (Phase 1) before continuing. Never let a deploy silently discard it.
3. **If the only difference is your intended change**, proceed to Phase 3.

## Phase 1 — Sync the box's checkout

The phase that prevents the silent-no-op `cp`. You cannot copy the new file onto the box
until the box's checkout actually holds it.

1. **SSH in:**
   ```bash
   ssh USER@192.168.1.118        # or USER@10.8.0.1 over WireGuard
   ```
2. **Go to the checkout** (clone it once if the box has none):
   ```bash
   cd ~/localDNS || git clone <repo-url> ~/localDNS && cd ~/localDNS
   ```
3. **Confirm a clean tree — don't clobber box-side drift:**
   ```bash
   git status -sb && git stash list
   ```
   Uncommitted changes here are drift to reconcile in Phase 2 — note them; don't discard
   them yet.
4. **Fetch and get onto the intended ref** (normally `main`; a not-yet-merged change is
   the exception — check out that branch, then land it on `main` per golden rule 5):
   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   ```
5. **Sanity-check you have the commit you pushed:**
   ```bash
   git log --oneline -1
   ```

## Phase 0 — Preflight in the repo

Before you touch the box, make the change real and know exactly where it goes.

1. **Land the change in git.** Commit and push it. Repo convention is straight to `main`
   (CLAUDE.md § 3); if it's on a branch, prefer merging to `main` before you deploy so
   the box tracks `main`.
2. **Green the doc check** so the repo is internally consistent:
   ```bash
   python3 tools/check-docs.py
   ```
3. **Look up each changed file's system path + reload command** in the
   [CLAUDE.md § C deploy table](../CLAUDE.md#c-deploy-paths). If a file has **no § C
   row**, it isn't deployable as written — add the row (repo path → system path →
   reload) first, so the mapping is never improvised at deploy time.

---

## Worked example — the Unbound loopback tighten

The change that motivated this protocol: binding Unbound to `127.0.0.1` instead of
`0.0.0.0` in `01-core-network/unbound/server.conf`. All phases, in execution order.

**Phase 0 — Preflight.** Committed the one-line `interface:` change and pushed;
`python3 tools/check-docs.py` green; § C row confirms
`01-core-network/unbound/server.conf` → `/etc/unbound/unbound.conf.d/server.conf`,
reload `sudo systemctl restart unbound`.

**Phase 1 — Sync the checkout.** `cd ~/localDNS`, `git status -sb` clean, then
`git fetch origin && git pull --ff-only`. *(The first attempt at this deploy skipped
Phase 1 and ran `cp` from `~` — `cp: cannot stat …`; the restart then reloaded the old
`0.0.0.0` file and looked healthy. Exactly golden rule 1.)*

**Phase 2 — Diff.** `diff /etc/unbound/unbound.conf.d/server.conf
~/localDNS/01-core-network/unbound/server.conf` — only the intended `interface:` line
differed; nothing box-only to reconcile.

**Phase 3 — Back up, deploy, validate, reload.** Backed up the live file, `sudo cp` the
repo file over it, `sudo unbound-checkconf` → *no errors*, then
`sudo systemctl restart unbound`.

**Phase 4 — Verify the effect.** `sudo ss -ulnp | grep 5335` now showed **only**
`127.0.0.1:5335` (not `0.0.0.0`); `dig @127.0.0.1 -p 5335 example.com +short` and
`docker exec pihole dig @127.0.0.1 -p 5335 example.com +short` both resolved — resolver
closed to the LAN, Pi-hole path intact.

**Phase 5 — Record + branch hygiene.** Box and repo confirmed matching; noted the box
should return to `main` once the change merges off its feature branch.
