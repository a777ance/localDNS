---
description: Front-door refresh — ask keep-history vs. clear first, then refeed the latest CLAUDE.md down the chosen path
allowed-tools: AskUserQuestion, Bash(git fetch:*), Bash(git log:*), Bash(git status:*), Read
---

The user wants this session on the latest CLAUDE.md. **Ask first — do not clear or
read anything yet.** This is the gate that a bare `/clear` can't offer (by the time
`/clear`'s hook runs, the conversation is already gone).

## 1. Ask how (one AskUserQuestion, header "Refresh")

- **Refeed in place (Recommended)** — keep the whole conversation; reload the latest
  briefing on top of it. Nothing is lost.
- **Clear + refeed** — wipe the conversation first for a clean slate, then reload.
  In-flight work in this chat is discarded.

## 2. If "Refeed in place" → do it now, no clear

Run the `/refeed` logic directly, conversation intact:

1. `git fetch origin --quiet` (read-only), then compare local vs. remote CLAUDE.md
   revision (`git log -1 --format='%h %ci' -- CLAUDE.md` for each).
2. If remote is ahead of local, stop and say so — the on-disk copy needs
   `git pull --ff-only` first. Otherwise continue.
3. Read the four-file manifest in one batch: `CLAUDE.md`, `README.md`,
   `docs/ai-cto/context.md`, `docs/architecture/network-context.md`.
4. Confirm in one line: the loaded CLAUDE.md revision + "refed in place, history
   kept." Then stop and wait for work.

## 3. If "Clear + refeed" → hand off to /clear

You cannot invoke `/clear` yourself — it's a built-in the user must type. Say exactly:

> Type `/clear` now — the SessionStart hook will auto-run the sync and refeed.

Then stop. Do not read the manifest here; the hook does it on the fresh session.
