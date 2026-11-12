# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py orient.probe` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-12, about 01:05 UTC · work lands on `leader` · `main` is emptied (`646c709`) · gate mode is `warn`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: none · expiry: none (no lease is running; the founder is in the loop)
- **Open decisions:** DEC-005
- **Open stalls:** none
- **Last five commits:**
  - fed4184 Merge pull request #47 from a777ance/claude/serene-tesla-yvl22m
  - d0ff063 DEC-016 executed: main is emptied (646c709, by the founder); records brought current
  - ff3c944 Merge pull request #46 from a777ance/claude/serene-tesla-yvl22m
  - 6744310 branches.md: all six meanings of the empty centre, each as a parable; record the founder's correction
  - 0266471 Merge pull request #45 from a777ance/claude/serene-tesla-yvl22m
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

DEC-005 only (venv files: needs two facts from the XPS; the command is in `docs/ai-cto/roadmap.md`).
`enforce` mode has no decision open and must not be turned on without one.

## Next work, in order

**The queue is `docs/ai-cto/handoff.md`, Q-031 to Q-042.** Start at Q-042 (the default branch), then Q-031.

- For the founder, in plain English: `docs/ai-cto/roadmap.md`.
- What past sessions shipped, got wrong, and learned: `docs/ai-cto/session-log.md`.
- Goals: `docs/ai-cto/initiatives.md`. Known flaws: `docs/ai-cto/debt.md`. Decisions: `docs/ai-cto/blocked.md`.

## Not yet seen live

A fresh session on `leader` showing a `cardinal:` line (it needs the default branch changed first); a fresh cloud container running the trimmed
setup script; a Stop-hook bounce; a compaction that uses the `PreCompact` text; the laptop timer.
