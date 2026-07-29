---
description: Lossless refeed — reload the latest on-disk CLAUDE.md and the canonical briefing manifest after a /clear
allowed-tools: Bash(git fetch:*), Bash(git log:*), Bash(git status:*), Read
---

You have just been cleared. Re-establish the working briefing **from disk** so this
session is running on the *latest* CLAUDE.md, not a stale in-context copy. Do this
fast and losslessly — read the whole manifest, drop nothing, add nothing.

## 1. Prove you have the latest

Run these (read-only — never merge or check out here; the founder pushes to `main`):

```bash
git fetch origin --quiet 2>/dev/null || true
git log -1 --format='local  %h  %ci  %s' -- CLAUDE.md
git log -1 --format='remote %h  %ci  %s' origin/HEAD -- CLAUDE.md 2>/dev/null || true
git status --short -- CLAUDE.md
```

If the **remote** CLAUDE.md is newer than **local**, stop and tell me — the on-disk
copy is behind and needs `git pull --ff-only` before the refeed means anything.
If they match (or there's no remote), the working tree is the latest — continue.

## 2. Read the lossless manifest (in one batch)

Read all of these from the working tree, in parallel:

1. `CLAUDE.md` — the authoritative briefing. Non-negotiable; this is the whole point.
2. `README.md` — top-level map + field-guide links.
3. `docs/ai-cto/context.md` — current component status and open items (the live state).
4. `docs/architecture/network-context.md` — rationale for the non-obvious decisions.

These four **are** the lossless set. Anything else (INSTALL-NOTES, SKILLS,
statements tooling) is pulled on demand, not part of the standing briefing.

## 3. Confirm ready — one line

Report exactly: the CLAUDE.md revision you loaded (`<short-hash> <date>`), that all
four manifest files were read, and any drift you noticed between them (e.g. the
ai-cto stage numbers vs. the CLAUDE.md deploy table). Then stop and wait for work.
Do not summarize the manifest back to me — just confirm the feed is fresh.
