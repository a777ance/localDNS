# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py orient.probe` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-12, about 02:00 UTC · work lands on `leader` · `main` is emptied (`646c709`) · gate mode is `warn`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: none · expiry: none (no lease is running; the founder is in the loop)
- **Open decisions:** DEC-019, DEC-018, DEC-005
- **Open stalls:** none
- **Last five commits:**
  - 31f17be Thirty leans for the end-to-end build, ranked and sorted into five tiers
  - edce654 DEC-019: the sub-loop hand-out for L items was stopped by the platform's safety system; record it as the founder's choice
  - add23bf Stop hook: an L item with a sub-loop already running is not handed out twice
  - d0a238f Merge pull request #57 from a777ance/claude/serene-tesla-yvl22m
  - 61610df The L step: what is left open goes under L, and each loop-owned item starts a sub-OODA loop at once
<!-- live:end -->

In prose:

- **Three branches (DEC-015, DEC-016).** `main` is emptied and is intent cold storage; `leader` takes
  all work; `outer` is the home for non-OODA files. See `docs/ai-cto/branches.md`.
- **The Matrix is on `leader` and live.** Labels and a stopwatch on every tool call, seven reply
  rules enforced by the Stop hook, nine gates on every commit. Mode is `warn`: nothing is blocked.
- **1 + N lanes (INIT-006), rehearsal (DEBT-012), and retrofit (INIT-007) are built.** The probe
  goes first; a command for the founder is run first; a new rule is applied to what already exists.
- **No lease is running.** The founder is in the loop. The first lease's "founder lease" and
  "Orchestrator lease" both ended on 2026-11-12; ignore any older text that cites them.
- **No PR is open and none is watched.**
- **No peers are running.** All eight from 2026-11-11 are archived.

## Open founder decisions

DEC-019 (how sub-loops run), DEC-018 (attach the repo to the scheduled loop, which is paused), and DEC-005 (venv files: needs two facts from the XPS; the command is in `docs/ai-cto/roadmap.md`).
`enforce` mode has no decision open and must not be turned on without one.

## Next work, in order

**The queue is `docs/ai-cto/superqueue.md`.** Start at its first open item in the loop's lane.
Why it is in that order: `docs/ai-cto/dependency-map.md`. The thirty leans behind it: `docs/ai-cto/leans-e2e.md`.

- For the founder, in plain English: `docs/ai-cto/roadmap.md`.
- What past sessions shipped, got wrong, and learned: `docs/ai-cto/session-log.md`.
- Goals: `docs/ai-cto/initiatives.md`. Known flaws: `docs/ai-cto/debt.md`. Decisions: `docs/ai-cto/blocked.md`.

## Not yet seen live

A compaction that uses the `PreCompact` text; `enforce` mode (the founder's hand only); the laptop
timer; the corrected setup script in a fresh container (its first version was seen working).
