# Handoff: the MVP, for a new cloud session (2026-11-12)

This file is the single handoff. It replaces the older handoff files in this folder for any new session.
Read it, then the superprompt below, then the thirty leans in docs/ai-cto/MVP-LEANS-30.md.

## Housekeeping before any work (check these first)

1. Repo state: the working tree is clean, and leader matches origin/leader (both at af3103f when this was written).
2. Full gate: run bash tools/check-all.sh. It must pass 25 of 25 steps before anything changes.
3. CLAUDE.md is 59,997 bytes against a 60,000-byte budget. Any edit that grows it fails check-registers.
   Decide DEC-022 first (shrink sections G and H), or do not grow CLAUDE.md.
4. The factory state is stale. Its next milestone is M23 with 2,352,878 tokens already spent. A new session
   must not inherit that budget. Reset the state only on the founder's word, and set a new budget explicitly.
5. The agent ledger is clean: 22 launched, 22 finished. A new session launches its own ledger from zero.
6. Open founder decisions: DEC-023, DEC-022, DEC-021, DEC-019, DEC-018, DEC-005 (in docs/ai-cto/blocked.md).

## What exists, and where

- Leans for the MVP, ranked: docs/ai-cto/MVP-LEANS-30.md
- Queue (the one the hooks read): docs/ai-cto/superqueue.md
- Decisions log: docs/ai-cto/blocked.md
- Branch rules: docs/ai-cto/branches.md (leader takes all work; main is intent only; outer for non-OODA files)
- The Matrix (the router and the gates): tools/matrix.py, configured by .claude/cardinal-map.json; the hooks are .claude/hooks/
- One entry point for health and preflight: tools/check-all.sh (use --quick for the fast profile)
- The software factory: tools/factory.sh (a bounded shell loop; it hands off to the session for each agent launch)
- The racetrack arena and planner: tools/racetrack.py and tools/racetrack_plan.py
- Race and factory results: docs/ai-cto/fleet/racetrack/RESULTS.md, COURSE-30-REVIEW.md, V3-QUALITY.md, RACE4-REVIEW.md
- The preflight that every run must pass: docs/ai-cto/fleet/racetrack/RULES.md
- The product's own rules: CLAUDE.md, and the field guide linked from README.md

## What is known about how the work runs

- Every run is preceded by the preflight in RULES.md, then probes. The Matrix probes are `observe.probe push`, `orient.probe` and `decide.probe`.
- Every commit passes a gate. A gate failure blocks the commit, and the fix is to repair the cause, never to bypass it.
- The Stop hook enforces the reply rules: the reply opens with a state word (Done, Partial, Blocked or Waiting), and ends with a single line `**Landed · N = <count>:**` with where each item stands.
- Agent launches are recorded with `python3 tools/matrix.py observe.agents finish ID` after each one completes; `check-all` fails while any launch has no finish.
- Measured: a sequential run is cheapest per finding (about 0.21 findings per 1k tokens); parallel-8 costs about four times the tokens for about 17% more findings (docs/ai-cto/fleet/racetrack/RESULTS.md).
- A $5 lease is about 2.4 million tokens at the output-rate estimate. The dollar rate is still unconfirmed.

## Superprompt (paste this into the new session)

You are the working session for the MVP of localDNS: one real, measured Network Activity Statement for one
household, produced end to end from the box, through the composer and the gates, into a document a person
keeps. Work on branch leader; never push to main; open a draft pull request for any branch you push, unless
one already exists.

Do, in order:
1. Read docs/ai-cto/HANDOFF-MVP.md and docs/ai-cto/MVP-LEANS-30.md. Do not re-derive the state from memory.
2. Run bash tools/check-all.sh. If anything fails, fix its cause first. Nothing else starts on a red gate.
3. Take the highest-ranked lean that a session can do alone (tagged [loop] in the leans file), and do it
   as a small, verified change. Ship it with the Matrix probe first, then push.
4. Do not do any [you] item. Those need the founder's hand: deploying to the t630, minting or sealing secrets,
   changing GitHub settings, deleting branches, rotating keys, and every founder decision in blocked.md.
5. Keep the reply rules: state word first, the landing line last. Name every decision you need as a DEC entry
   in docs/ai-cto/blocked.md and stop there; do not choose for the founder.
6. Stop when the next item is blocked on the founder, or the work is done. Say which, in one line, and why.

Hard rules: no destructive shell (no forced pushes, no hard resets, no recursive deletes); no polling of PR or
CI state; no model names in any file or commit; no real customer data in git; the Statement prints only what
the box measured.

## Next actions in order (the first three are [loop] and need no founder)

1. Fix the budget check in tools/factory.sh so it predicts the next launch's cost before handing off (lean 21).
2. Make the superfleet and racetrack gates fail closed on empty inputs (lean 19).
3. Fix the fail-open paths in .claude/hooks/timing.py, resume.py and precompact.py (lean 18).
Then wait on the founder for the [you] items in the leans file, starting with lean 1.
