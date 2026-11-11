# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py observe.status` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-11, about 23:02 UTC (end of the Orchestrator lease's work) · branch `decision-log-dec007` · PR #37 (draft, unmerged)

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `decision-log-dec007`
- **Lease:** start: 22:52 UTC (2026-11-11) · expiry: 01:52 UTC (2026-11-12)
- **Open decisions:** DEC-014, DEC-013, DEC-012, DEC-011, DEC-010, DEC-005
- **Open stalls:** none
- **Last five commits:**
  - 65a36de Q-025, Q-026: DEC-013 and DEC-014 tiles; record measurements, debt, and progress
  - 9dbb09b Q-024: end-to-end test for the telepathy mailbox; map its tools into the Matrix
  - 74d0e40 Q-014 to Q-019, Q-022, Q-023: mechanize the reply rules; gate the registers; clear DEBT-006
  - c1ea0ef Q-011, Q-020, Q-021: time native tool calls; steer the compaction summary; wake on resume and fork
  - 52ecd1b Q-005 to Q-010, Q-012, Q-013: bound, back up, and measure the Matrix's own tooling
<!-- live:end -->

Background from the handoff:

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

## Q-001 · hooks observed live in the Orchestrator session (2026-11-11, 22:53 UTC)

- `Read` call: the hook returned `cardinal: observe.read`.
- Bash call: the hook returned `cardinal: decide.gate` (start commands) and `cardinal: observe.read` (a read-only compound).
- Stop-hook bounce: **not observed live.** Proving it means ending a turn on a deliberately
  bad reply; if the hook did not fire, the lease would stop there. Q-014 tests the hook by
  feeding it replies directly.
- **Orchestrator lease:** 22:52 UTC to 01:52 UTC.

## Open founder decisions

DEC-012 (warn mode), DEC-011 (merge PR #37), DEC-010 (scope the tile rule), DEC-005 (venv
files). DEC-004 and DEC-006 are moot: PR #36 is merged.

## Next work, in order

**For the founder, in plain English: `docs/ai-cto/roadmap.md`.**

The queue in `docs/ai-cto/handoff.md` is worked through: 25 of the 26 unblocked items are
`DONE` with their commit, Q-004 is `SKIPPED` (usage limit), and Q-027 to Q-030 wait on the founder.

1. Founder decisions, newest first: DEC-014 (trim the setup script), DEC-013 (split `CLAUDE.md`),
   DEC-012 (`warn` mode), DEC-011 (merge PR #37), DEC-010 (tile scope), DEC-005 (venv files).
2. Q-004, once usage allows: spawn one `juror` and look for `· agent: juror` in a cardinal line
   or a row in `.claude/.matrix-times`. Record the result in DEBT-008.
3. DEBT-011: six lint findings that predate this work.
4. At the next compaction, check that the summary carries the lease and decision lines from
   `.claude/hooks/precompact.py`. That hook has only been tested by piping input into it.
