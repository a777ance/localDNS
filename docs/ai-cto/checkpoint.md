# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py observe.status` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-11, about 23:55 UTC · `main` is at `67da1b6` plus this change · gate mode is `warn`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: 22:52 UTC (2026-11-11) · expiry: 01:52 UTC (2026-11-12)
- **Open decisions:** DEC-005
- **Open stalls:** none
- **Last five commits:**
  - 67da1b6 DEC-012: gate mode to warn
  - 253d0d8 Merge pull request #38 from a777ance/claude/serene-tesla-yvl22m
  - 383c057 Fix check-matrix.py failing whenever the live gate mode is warn
  - 7a40e52 Record DEC-011 and DEC-014 as executed; update the roadmap and checkpoint after the merge
  - 60a53d7 Merge pull request #37 from a777ance/decision-log-dec007
<!-- live:end -->

Background from the handoff:

- **The Matrix (INIT-005) is built and tested on the branch.** Map `.claude/cardinal-map.json`,
  four cardinal skills, naming hook `.claude/hooks/cardinal.py`, own tooling `tools/matrix.py`,
  gates `tools/check-cardinal.py` and `tools/check-matrix.py`. Gate mode is `name` (nothing blocked).
- **On `main` since 2026-11-11** (merge `60a53d7`).
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

DEC-012 is done (mode is `warn`, set by the founder, `67da1b6`). Open: DEC-005 (venv files: needs two facts from the XPS). The leans are in
`docs/ai-cto/leans.md`.

## Next work, in order

**For the founder, in plain English: `docs/ai-cto/roadmap.md`.**

1. In a fresh session on `main`, look for a `cardinal:` line on the first tool call. That is
   the proof the merge reached new sessions (Q-027).
2. In a fresh cloud container, read the setup log for nine `ok` lines from `decide.gate`.
   The trimmed script was run by hand once; a fresh container has not run it yet.
3. DEBT-011: two unused variables in `compose.py`.
4. At the next compaction, check the summary carries the lines from `.claude/hooks/precompact.py`.
   The wake-up hook `.claude/hooks/resume.py` was seen firing live on a session resume, 2026-11-11.
