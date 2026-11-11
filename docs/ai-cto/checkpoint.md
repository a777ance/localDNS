# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py observe.status` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-11, about 23:35 UTC · PR #37 is merged into `main` as `60a53d7` · follow-up work is on branch `claude/serene-tesla-yvl22m`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: 22:52 UTC (2026-11-11) · expiry: 01:52 UTC (2026-11-12)
- **Open decisions:** DEC-012, DEC-005
- **Open stalls:** none
- **Last five commits:**
  - 60a53d7 Merge pull request #37 from a777ance/decision-log-dec007
  - fa94d93 DEC-013 and DEC-010: shrink CLAUDE.md by 10,000 bytes, scope the tile rule; record 20 leans
  - 83937ef Map SubagentHandback (seen unmapped in the live subagent run); correct the Q-004 time
  - 482d34d Q-004: confirm live that the naming hook fires inside a subagent and names it
  - 996ce7f Add a plain-English roadmap for the founder; fix the cloud-only cd path at its source
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

DEC-012 (`warn` mode: lean GO, but a session may not flip its own gate; needs the founder's
hand) and DEC-005 (venv files: needs two facts from the XPS). The leans are in
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
