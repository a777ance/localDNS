# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py observe.status` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-11, about 22:50 UTC (handoff to the Orchestrator session) · branch `decision-log-dec007` · PR #37 (draft, unmerged)

## Where things stand

- **The Matrix (INIT-005) is built and tested on the branch.** Map `.claude/cardinal-map.json`,
  four cardinal skills, naming hook `.claude/hooks/cardinal.py`, own tooling `tools/matrix.py`,
  gates `tools/check-cardinal.py` and `tools/check-matrix.py`. Gate mode is `name` (nothing blocked).
- **Not on `main`.** New sessions get none of it until PR #37 merges (DEC-011).
- **Founder lease:** unattended work until about 01:28 UTC on 2026-11-12. Covers building and
  pushing to the branch. Does not cover merging to `main` or changing the gate mode.
- **Peers:** all eight peer sessions this session created are finished and archived
  (2026-11-11, about 22:33 UTC). None is running. Their combined cost was about $12.80.
- **Stop hook** now also requires each reply to open with a bold state word (the one rule
  the Carrot pair proposed before they were stopped).

## Open founder decisions

DEC-012 (warn mode), DEC-011 (merge PR #37), DEC-010 (scope the tile rule), DEC-005 (venv
files). DEC-004 and DEC-006 are moot: PR #36 is merged.

## Next work, in order

**The roadmap is `docs/ai-cto/handoff.md`.** It holds the founder's intent, the rules of
engagement for the 3-hour lease, research notes on hooks, and a queue of 30 items (Q-001 to
Q-030). Start at Q-001. Items Q-027 to Q-030 wait on founder decisions.
