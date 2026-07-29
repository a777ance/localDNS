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

One-liner: **sync → clear → `/refeed`.**

---

## Contents

Blocks run last-first per house style (execution order is fixed by the stage
numbers, not by reading order — Stage 1 runs first even though it's listed last).

- [Stage 3 — Refeed](#stage-3--refeed)
- [Stage 2 — Clear](#stage-2--clear)
- [Stage 1 — Sync](#stage-1--sync)
- [The lossless manifest](#the-lossless-manifest)
- [Guarantees & limits](#guarantees--limits)
- [Revision log](#revision-log)

---

## Stage 3 — Refeed

Re-seed the standing briefing from disk. This is the "lossless" step — it reloads the
whole [manifest](#the-lossless-manifest), not only the file Claude Code re-injects on
its own.

1. Run `/refeed` (the project slash command in `.claude/commands/refeed.md`).
2. It fetches read-only, prints the CLAUDE.md revision it loaded, and reads all four
   manifest files in one batch.
3. It stops on a one-line "feed is fresh" confirmation naming the revision. If it
   reports the remote CLAUDE.md is ahead of local, go back to **Stage 1** and pull —
   the clear happened against a copy that was already behind.

Manual fallback (no slash command available): read the four manifest files yourself,
top to bottom, starting with CLAUDE.md.

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
- **Latest-or-it-says-so** — Stage 1 makes staleness visible; `/refeed` refuses to
  pretend a behind-local copy is current. If remote is ahead, it tells you to pull
  rather than seeding stale.

---

## Revision log

- **2026-07-29** — Protocol created. Three-stage sync → clear → `/refeed` ritual, the
  four-file lossless manifest, and the `.claude/commands/refeed.md` slash command.
