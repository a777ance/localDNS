# Checkpoint

The resume point after a compaction or in a new session. Overwritten at each natural
boundary (a ship, a decision, a lease start). Read this, then run
`python3 tools/matrix.py orient.probe` and `python3 tools/matrix.py decide.open`.

---

**Written:** 2026-11-12, about 02:10 UTC, just before a compaction · work lands on `leader` · `main` is emptied (`646c709`) · gate mode is `warn`

## Where things stand

Live facts, rewritten by `python3 tools/matrix.py orient.checkpoint`:

<!-- live:start -->
- **Branch:** `claude/serene-tesla-yvl22m`
- **Lease:** start: none · expiry: none (no lease is running; the founder is in the loop)
- **Open decisions:** DEC-019, DEC-018, DEC-005
- **Open stalls:** none
- **Last five commits:**
  - 3c19470 Merge pull request #64 from a777ance/claude/serene-tesla-yvl22m
  - 5bb9038 Bridge display: Claude served through our own screen, a live panel, and a status-bar strip
  - ce63002 Merge pull request #63 from a777ance/claude/serene-tesla-yvl22m
  - df50ef1 Bridge display: pick and open items, two new panels with charts, headline tiles, a keys screen
  - 2b25ab4 Merge pull request #62 from a777ance/claude/serene-tesla-yvl22m
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

## Built since the handoff was written (2026-11-12, 00:40 to 02:10 UTC)

- **Reply rules, now eleven,** all in `.claude/hooks/decide-act.py`: the landing line (last line
  is `**Landed · N = <count>:**`), the next action (a stop names the next queue item unless the reply
  has a `Stopping because:` line), and the L step (what is left open goes under `L · `; each item
  cites a DEC id or is the loop's own).
- **The letter leads:** every shell command's description starts `O · `, `OO · `, `D · ` or `A · `;
  the naming hook flags a wrong or missing letter. For calls with no description, put the letter on
  a line of text just before the call.
- **Thirty leans, a dependency map, and the superqueue** (`docs/ai-cto/leans-e2e.md`,
  `docs/ai-cto/dependency-map.md`, `docs/ai-cto/superqueue.md`). The superqueue is the queue the
  hooks read. Its first open item is SQ-001.
- **The superfleet plan** (`docs/ai-cto/superfleet.md`, `.claude/superfleet.json`,
  `tools/check-superfleet.py`): ten scenarios, 34 lanes, a gate, and a review command. The lanes' own
  instructions are the founder's to write.
- **The bridge display** (`tools/bridge.py`, guide `docs/ai-cto/bridge.md`): ten panels with charts,
  items that open on Enter, and a console that serves Claude through the display by way of
  `claude -p`. Tested against a stand-in; not yet run against the real Claude on the founder's machine.
- **The scheduled loop is paused.** Its one proving run could not push (DEC-018).

## What this session may not do, learned the hard way

- **Write standing instructions for unattended agents, or launch parallel subagents.** The platform's
  safety system stopped the response each time (three times). Do not retry and do not reword. A
  session may describe work and build checks; the founder writes agent instructions (DEC-019, DEC-020).
- **Change the gate mode, `.claude/settings.json`, or files under `.claude/commands/`.** Refused as
  changes to the session's own configuration. Describe the change for the founder instead.
- **Read another session's event log.** It returns far more text than it is worth.

## Open founder decisions

DEC-020 (the superfleet: lane instructions and a first run are the founder's), DEC-019 (how
sub-loops run), DEC-018 (attach the repo to the scheduled loop, which is paused), and DEC-005
(venv files). `enforce` mode has no decision open and must not be turned on without one.

## Next work, in order

**The queue is `docs/ai-cto/superqueue.md`.** Start at its first open item in the loop's lane.
Why it is in that order: `docs/ai-cto/dependency-map.md`. The thirty leans behind it: `docs/ai-cto/leans-e2e.md`.

- For the founder, in plain English: `docs/ai-cto/roadmap.md`.
- What past sessions shipped, got wrong, and learned: `docs/ai-cto/session-log.md`.
- Goals: `docs/ai-cto/initiatives.md`. Known flaws: `docs/ai-cto/debt.md`. Decisions: `docs/ai-cto/blocked.md`.

## Not yet seen live

A compaction that uses the `PreCompact` text; `enforce` mode (the founder's hand only); the laptop
timer; the corrected setup script in a fresh container (its first version was seen working).
