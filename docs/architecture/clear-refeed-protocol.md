# Clear & Refeed Protocol

A three-stage ritual for wiping a stale conversation and re-seeding it, **rapidly**
and **losslessly**, so the session is always driven by the *latest* CLAUDE.md rather
than the copy that happened to be injected when the session opened.

**Why this exists.** CLAUDE.md is read once, at session start, and pinned into
context. If it's edited mid-session — by you, another session, or a founder push —
the running assistant keeps quoting the *old* briefing until the context is cleared.
`/clear` drops that stale copy; the refeed re-seeds the current one. "Lossless" means
the re-seed restores the full standing briefing (the manifest below), not just the
single file Claude Code auto-reinjects.

One-liner: **sync → clear → refeed** — or, with the hook installed, just **`/clear`**
and the other two happen for you. For a mid-session refresh *without* clearing, one
command does both the sync and the reseed: **`/repull`** (it pulls `--ff-only` on `main`,
then re-reads the manifest).

---

## Contents

Blocks run last-first per house style (execution order is fixed by the stage
numbers, not by reading order — Stage 1 runs first even though it's listed last).

- [Front door: choose before you wipe (`/refresh`)](#front-door-choose-before-you-wipe-refresh)
- [The one-command path (SessionStart hook)](#the-one-command-path-sessionstart-hook)
- [Stage 3 — Refeed](#stage-3--refeed)
- [Stage 2 — Clear](#stage-2--clear)
- [Stage 1 — Sync](#stage-1--sync)
- [The lossless manifest](#the-lossless-manifest)
- [Guarantees & limits](#guarantees--limits)
- [Revision log](#revision-log)

---

## Front door: choose before you wipe (`/refresh`)

`/clear` is unconditional — it wipes first and asks nothing. If you want a **yes/no
gate before losing history**, that gate can't live on `/clear` (the built-in offers
no pre-wipe interception, and the `SessionStart` hook only runs *after* the clear has
already happened). It has to live in a **front-door command you type instead of
`/clear`**: `.claude/commands/refresh.md`.

`/refresh` asks once, then branches:

- **Refeed in place** (default) — keeps the whole conversation and reloads the latest
  briefing on top of it. This is the auto-funnel: answer "don't clear" and it runs the
  refeed for you, no wipe, no second command.
- **Clear + refeed** — a custom command can't invoke the built-in `/clear`, so this
  branch hands off: it tells you to type `/clear`, and the hook takes it from there.

Use `/refresh` when you might want to keep history; type `/clear` directly when you
already know you want the clean-slate end-to-end path.

## The one-command path (SessionStart hook)

The three stages below are the manual ritual. To collapse them into a **single
command**, the repo ships a `SessionStart` hook (`.claude/hooks/refeed.sh`, wired in
`.claude/settings.json`) that fires automatically whenever a session starts fresh or
is cleared. When it fires it runs Stage 1 (sync: `git fetch` + a guarded
fast-forward pull) and Stage 3 (refeed: injects the manifest directive), so:

> **`/clear` is the end-to-end command.** You type `/clear`; the hook does the sync
> and the refeed around it. One keystroke = sync → clear → refeed.

Why it's a hook and not a `/`-command: a slash command's body runs *inside the
conversation it would clear*, so a single command can't clear itself and then keep
running. The `SessionStart` hook is the only place the sync+refeed can execute
*around* the clear rather than inside it.

Scope and safety:

- Runs only on `source=startup` and `source=clear`. On `resume`/`compact` it exits
  immediately — no pull, no re-inject — so in-progress work is never disturbed.
- The pull is **fast-forward only and skipped on a dirty tree**. If it can't safely
  fast-forward, it injects a `sync: BEHIND …` note instead of forcing anything.
- It never re-injects CLAUDE.md (Claude Code reloads that from disk on every
  clear); it only pulls in the *other three* manifest files.

`/repull` (the slash command, formerly `/refeed`) is the **no-clear** case — refreshing
the briefing mid-session without wiping the conversation. Because a bare re-read reloads
*stale* files when local is behind, it **pulls `--ff-only` on `main` first**, then reads
the manifest — folding Stage 1's sync into the command so the no-clear path can't seed
stale.

---

## Stage 3 — Refeed

Re-seed the standing briefing from disk. This is the "lossless" step — it reloads the
whole [manifest](#the-lossless-manifest), not only the file Claude Code re-injects on
its own.

1. Run `/repull` (the project slash command in `.claude/commands/repull.md`).
2. It **pulls `--ff-only` on `main`** to land the latest on disk (skipped on a dirty or
   diverged tree — it stops and says so rather than seeding stale), prints the CLAUDE.md
   revision it landed, and reads all four manifest files in one batch.
3. It stops on a one-line "feed is fresh and on the latest" confirmation naming the
   revision and whether the pull fast-forwarded or was already current.

Manual fallback (no slash command available): `git pull --ff-only` on a clean tree, then
read the four manifest files yourself, top to bottom, starting with CLAUDE.md.

---

## Stage 2 — Clear

Drop the stale in-context briefing.

1. Run `/clear`. This wipes the conversation, including the CLAUDE.md snapshot pinned
   at session start.
2. Do **not** rely on the auto-reinjected CLAUDE.md alone — it's the current file, but
   it is *only* CLAUDE.md. The derived context (README map, live AI-CTO state, design
   rationale) is gone until Stage 3 restores it. That gap is exactly what makes a bare
   `/clear` lossy.

---

## Stage 1 — Sync

Make the on-disk CLAUDE.md the latest before you clear against it. Clearing against a
stale working tree just reloads stale — order matters.

1. `git fetch origin` — see whether anything landed since this session opened.
2. `git log -1 --format='%h %ci %s' -- CLAUDE.md` locally, and the same against
   `origin/HEAD`, to compare revisions.
3. If remote is ahead: `git pull --ff-only` on `main` (founder pushes straight to
   `main` — no branches). If they match, the working tree is already latest — proceed.

---

## The lossless manifest

The four files that constitute a complete standing briefing. Read together, they lose
nothing a fresh session would have had. Listed Z→A per house style; read CLAUDE.md
first regardless.

| File | Role in the briefing |
| ---- | -------------------- |
| `README.md` | Top-level map + interactive field-guide links |
| `docs/architecture/network-context.md` | Rationale for the non-obvious design decisions |
| `docs/ai-cto/context.md` | Live component status + current open items (the moving part) |
| `CLAUDE.md` | The authoritative summary of the whole system — always first |

Deliberately **out** of the manifest (pull on demand, keep the refeed fast):
`docs/architecture/INSTALL-NOTES.md`, `docs/architecture/SKILLS.md`, the
`docs/statements/` tooling, and per-service configs. Adding them would make the refeed
slower without changing which decisions the assistant can make from the standing set.

---

## Guarantees & limits

- **Rapid** — one fetch plus four reads, issued as a single batch. No file walk, no
  re-derivation from history.
- **Lossless** — every file in the standing briefing is restored, so nothing a fresh
  session would know is missing. It is *not* a memory of the cleared conversation:
  in-flight work, uncommitted reasoning, and scratch state are gone by design. Commit
  or note anything worth keeping **before** Stage 2.
- **Latest, not just latest-or-it-says-so** — `/repull` doesn't merely *flag* a
  behind-local copy, it **fixes** it: a `--ff-only` pull on `main` lands the latest on
  disk before the reseed, so the no-clear refresh can't reload stale files. It still
  refuses to force anything — a dirty or diverged tree stops with a note rather than
  seeding stale or clobbering in-flight work.

---

## Revision log

- **2026-08-03** — Renamed the no-clear command `/refeed` → `/repull`
  (`.claude/commands/repull.md`) and made it **pull `--ff-only` on `main` before
  reading** instead of a read-only fetch: a "refresh" is really a pull, so re-reading a
  behind-local tree reloaded stale files. `/refresh`'s in-place path pulls the same way.
- **2026-08-03** — Made the `SessionStart` hook emit the **§G lazy anchor first**: the
  fresh session opens by acting on the top "Default next actions" item, with the
  lossless manifest load demoted to "as the work demands it" so it can't anchor the
  trajectory into a read-everything preamble.
- **2026-07-29** — Added the `/refresh` front door: a pre-wipe Q&A gate
  (`.claude/commands/refresh.md`) that asks keep-history vs. clear, auto-running the
  in-place refeed on "keep" and handing off to `/clear` on "clear."
- **2026-07-29** — Added the one-command path: a `SessionStart` hook
  (`.claude/hooks/refeed.sh` + `.claude/settings.json`) that auto-runs sync + refeed
  on `startup`/`clear`, making bare `/clear` the end-to-end command.
- **2026-07-29** — Protocol created. Three-stage sync → clear → refeed ritual, the
  four-file lossless manifest, and the slash command now at `.claude/commands/repull.md`
  (created as `refeed.md`; renamed 2026-08-03).
