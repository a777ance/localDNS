---
description: Repull — fast-forward the latest onto disk (git pull --ff-only on main), THEN refeed the whole briefing manifest. The no-clear mid-session refresh.
allowed-tools: Bash(git fetch:*), Bash(git pull:*), Bash(git log:*), Bash(git status:*), Bash(git rev-parse:*), Read
---

Refresh the working briefing mid-session **without** clearing the conversation — and do
it against the *latest* CLAUDE.md, not the copy pinned when the session opened.

On this repo the founder pushes straight to `main`, so a "refresh" is really a **pull**:
a read-only re-read of the working tree faithfully reloads *stale* files whenever local
is behind `origin/main`. This command therefore **pulls first, then refeeds** — the same
sync-then-reseed the `SessionStart` hook does around a `/clear`, but for the no-clear case.

## 1. Pull the latest onto disk (fast-forward only)

```bash
git fetch origin --quiet
git status --short                            # must be clean to fast-forward
git log -1 --format='local %h %ci %s' -- CLAUDE.md
git pull --ff-only 2>&1                        # land origin/main on disk — no merge commit, no rewrite
git log -1 --format='now   %h %ci %s' -- CLAUDE.md
```

- **Dirty tree** → do **not** pull. Stop and tell me what's uncommitted, so a
  fast-forward can't clobber in-flight work. Commit or stash first, then re-run.
- **Non-fast-forward** (local has diverged from `origin/main`) → stop and tell me;
  don't force it. Reconcile by hand.
- **Already up to date** → fine, the working tree is already latest — continue to the refeed.

## 2. Read the lossless manifest (in one batch)

Read all of these from the **now-current** working tree, in parallel:

1. `CLAUDE.md` — the authoritative briefing. Non-negotiable; this is the whole point.
2. `README.md` — top-level map + field-guide links.
3. `docs/ai-cto/context.md` — current component status and open items (the live state).
4. `docs/architecture/network-context.md` — rationale for the non-obvious decisions.

These four **are** the lossless set. Anything else (INSTALL-NOTES, SKILLS,
statements tooling) is pulled on demand, not part of the standing briefing.

## 3. Confirm ready — one line

Report exactly: the CLAUDE.md revision you landed (`<short-hash> <date>`), whether the
pull **fast-forwarded** or was **already current**, and that all four manifest files were
read. Then stop and wait for work. Do not summarize the manifest back to me — just confirm
the feed is fresh **and on the latest**.
