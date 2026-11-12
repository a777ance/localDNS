# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py orient.probe` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-12, about 01:15 UTC · work lands on `leader` · `main` is emptied (`646c709`) · gate mode is `warn`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: none · expiry: none (no lease is running; the founder is in the loop)
- **Open decisions:** DEC-017, DEC-005
- **Open stalls:** none
- **Last five commits:**
  - deb778e Fix Statement percentages to sum to exactly 100; call out any push to main; stop git merge-base counting as egress
  - a1ebb4f Merge pull request #50 from a777ance/claude/statements-gate-9167a3
  - cc5d056 Add check-statements.py: a commit gate for the Statement honesty rule (INIT-004); two build_alloc faults reported, not fixed
  - 60dbdd2 Merge pull request #49 from a777ance/claude/serene-tesla-yvl22m
  - 9053d7a DEBT-008: a Stop-hook bounce and the egress flag were both seen live
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

DEC-017 (schedule the loop tick; it spends money) and DEC-005 (venv files: needs two facts from the XPS; the command is in `docs/ai-cto/roadmap.md`).
`enforce` mode has no decision open and must not be turned on without one.

## Next work, in order

**The queue is `docs/ai-cto/handoff.md`, Q-031 to Q-042.** Start at Q-034. Open for the founder: DEC-017 (schedule the loop tick) and DEC-005.

- For the founder, in plain English: `docs/ai-cto/roadmap.md`.
- What past sessions shipped, got wrong, and learned: `docs/ai-cto/session-log.md`.
- Goals: `docs/ai-cto/initiatives.md`. Known flaws: `docs/ai-cto/debt.md`. Decisions: `docs/ai-cto/blocked.md`.

## Not yet seen live

A compaction that uses the `PreCompact` text; `enforce` mode (the founder's hand only); the laptop
timer; the corrected setup script in a fresh container (its first version was seen working).
