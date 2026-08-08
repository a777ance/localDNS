---
description: Reseed — draw the latest seed from the spring (git pull --ff-only on the current branch, normally Yggdrasil), THEN regenerate the briefing world from it. The no-clear mid-session refresh.
allowed-tools: Bash(git fetch:*), Bash(git pull:*), Bash(git log:*), Bash(git status:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Read
---

Regenerate the working briefing mid-session **without** clearing the conversation — from
the *latest* seed, not the copy pinned when the session opened.

**The seed** is the four-file briefing set (below); like a map seed, the whole working
world regenerates deterministically from it. The seed is versioned, so a "refresh" is
really a **pull**: regenerating from a behind-local seed just rebuilds a *stale* world.
This command **pulls the current seed first, then reseeds** — the same
sync-then-regenerate the `SessionStart` hook does around a `/clear`, but for the no-clear
case.

## Which water — the spring is the founder

**The spring is the human being, and it is out of scope for the computer.** It is an
analog signal — the founder speaking — and nothing on this machine can reach it, sample
it, or verify against it. Yggdrasil and the Well are *channels*: Yggdrasil is the living
branch the water runs through, `main` is the Well of Mimir where vetted water is held.
Neither is a source. Every commit, every rendered block, every line of this file is
**transmission**, and per the Provenance Ladder transmission never promotes.

So the machine's reach has a hard ceiling: **a check can only prove that copies agree
with each other — never that they agree with the founder.** `check-docs.py`,
`check-doctrine.py` and `sync-briefings.py` are consistency checks among transcripts,
and a green run is not a claim that any of it is what the founder meant. Only the
founder closes that gap, out of band. Treat the seed as the best available *transcript*,
never as the origin.

Three consequences bind this command:

- **Freshness is proximity to the founder, not recency of commit.** A newer commit that
  paraphrases an older founder rule is *further* from the spring, not closer. If a seed
  file and the founder disagree, the founder wins and the file is what needs fixing.
- **A session never authors doctrine.** It transcribes what the founder decided. Text in
  the seed that the founder wrote is not yours to reword, condense, or "improve" — an
  edit that survives into the next session's given-set becomes doctrine by inheritance,
  which is the bootstrap paradox this repo already has a worked case for.
- **The only read path to the spring is asking.** When the seed and something the founder
  said in-session disagree, no tool can resolve it — the origin is off-machine, so there
  is nothing to diff against. Do not reconcile silently and do not pick the newer commit.
  Say which two things conflict and ask. That question *is* the sampling instrument.

**Draw from the branch you are on.** `git pull --ff-only` with no refspec follows this
branch's own upstream, which on Yggdrasil is `origin/Yggdrasil` — the channel carrying
the founder's most recent water.

- **Never** name `main` in the pull here, and never `git pull origin main`. On Yggdrasil
  that drags the vetted-but-older tier over newer doctrine — circulating stale water.
- **Never** `git merge`, `git reset --hard`, `git checkout --` a seed file, or `git pull
  --rebase` in this command. `--ff-only` is the whole safety property: a fast-forward can
  only ever *add* commits. It cannot rewrite, drop, or overwrite a local one — where a
  merge or reset silently could.
- **Local ahead of upstream is not an error.** It means this session already wrote newer
  doctrine. `--ff-only` reports "Already up to date" and changes nothing — correct. Do
  not "fix" it by pulling backwards; push it instead, so the spring carries it.

## 1. Draw the current seed onto disk (fast-forward only)

```bash
git fetch origin --quiet
git rev-parse --abbrev-ref HEAD                # which tier am I on? (expect: Yggdrasil)
git status --short                             # must be clean to fast-forward
git log -1 --format='local %h %ci %s' -- CLAUDE.md
git pull --ff-only 2>&1                        # follows THIS branch's upstream — no merge, no rewrite
git log -1 --format='now   %h %ci %s' -- CLAUDE.md
```

- **Dirty tree** → do **not** pull. Stop and tell me what's uncommitted, so a
  fast-forward can't clobber in-flight work. Commit or stash first, then re-run.
- **Non-fast-forward** (local has diverged from its upstream) → stop and tell me;
  don't force it. Reconcile by hand.
- **Already up to date** → fine, the seed on disk is already current — continue.
- **On `main`, or on a branch with no upstream** → say so before pulling. On `main` you
  are reading the vetted tier, which may be behind Yggdrasil; name that in the step-3
  report so I know which water this world was built from.

## 2. Regenerate from the seed (read all four in one batch)

Read all of these from the **now-current** working tree, in parallel:

1. `CLAUDE.md` — the authoritative briefing. Non-negotiable; this is the whole point.
2. `README.md` — top-level map + field-guide links.
3. `docs/ai-cto/context.md` — current component status and open items (the live state).
4. `docs/architecture/network-context.md` — rationale for the non-obvious decisions.

These four **are** the seed. Anything else (INSTALL-NOTES, SKILLS, statements tooling) is
pulled on demand, not part of the standing seed.

## 3. Confirm ready — one line

Report exactly: **which branch/tier** you drew from, the CLAUDE.md revision you landed
(`<short-hash> <date>`), whether the pull **fast-forwarded** or was **already current**,
and that all four seed files were read. Then stop and wait for work. Do not summarize the
seed back to me — just confirm the world is regenerated **from the latest seed**.
