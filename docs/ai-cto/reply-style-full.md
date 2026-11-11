# Reply style: Briefing — full text

The long form of the reply rules, moved here from `CLAUDE.md` on 2026-11-11 (DEC-013), unchanged.
`CLAUDE.md` keeps one line per rule and names the hook that enforces it.

Applies to every reply in this repo, regardless of output style. Mirrors
`.claude/output-styles/briefing.md`.

- **Lead state word first.** Open with a bold state word: **Done**, **Partial**,
  **Blocked**, or **Waiting**.
- **The Matrix (also: OODA matrix, alias net — three names, one thing). Motto: "There is no way out."**
  No tool call, workflow, or subagent runs outside it. Every tool call belongs to exactly one of the four cardinal skills
  (`.claude/skills/observe`, `orient`, `decide`, `act`) and is named as `cardinal.method`,
  for example `observe.read` or `act.ship`. Methods replace atomized skills. The map is
  `.claude/cardinal-map.json`; `tools/check-cardinal.py` is its gate.
- **Workflows follow the Matrix too.** Every rule here applies to tool calls made inside a
  workflow (subagents, parallel agents, Ultracode runs) exactly as it applies to a normal
  call: the cardinal name, the repoint, the 10-second cap, the lease, and the stall rule.
  A session with no checkout of this repo loads no hooks, so its prompt must carry the rules.
- **A Matrix stall is a defect, fixed at once.** Matrix calls have a 10-second hard cap. A
  breach writes a one-time lease for the native tool (so work is never roadblocked) and a
  stall incident. While a stall is open, diagnose why the alias stalled and improve it
  before other work: `python3 tools/matrix.py orient.stall`, then `act.resolve`.
- **Ten seconds is the Holy Grail.** Every tool call should finish in under 10 seconds.
  Shape tools and repo layout for that: one small call over one big one, narrow reads
  (`observe.read PATH START END`, `observe.search PATTERN PATH`) over whole-file dumps, and
  `decide.gate` prints each check's time and flags any over 10 s as debt.
- **Spend tokens like money; never idle.** Keep tool output short (ranges, `head`, counts).
  Never poll or wait in a loop: end the turn and let an event wake the session. Stop peers
  that return null results or run past their usefulness. Do not re-read what is on disk.
- **Compact strategically.** State lives on disk, not in the conversation, so compaction
  loses nothing: before a long stretch, and at each natural boundary (a ship, a decision,
  a lease start), update `docs/ai-cto/checkpoint.md`. After a compaction or in a new
  session, resume from that file plus `python3 tools/matrix.py observe.status`.
  `.claude/hooks/resume.py` (a `SessionStart` hook on `compact`) does this automatically:
  it re-injects the checkpoint, the Matrix status, and the open decisions, and tells the
  session to carry on without waiting.
- **Strike while the iron is hot.** Commit and push each finished piece the moment its
  gates pass, and always before a compaction, a long call, or the end of a turn. Work that
  exists only in the working tree or the conversation is state waiting to be lost.
- **Resolve stacked requests newest first, and drop none.** When several requests arrive
  mid-turn, work them in LIFO order and account for every one in the report.
- **Carrot.** The 3-hour lease for peer sessions is the Carrot. Name it by that word in
  peer prompts and in status lines. Assumed reading, stated in INIT-003: the Carrot lease is
  3 hours from the first ping, with UTC expiry.
- **OODA structure.** Observe (facts, with evidence) → Orient (meaning; name each assumption
  as `Assume:`) → Decide (options queued, numbered, never chosen between unless asked) →
  Act (run the queue or the first item, one line per result).
- **Orient reads from disk.** Before Orient, read `docs/ai-cto/initiatives.md` (goals and
  line items, `INIT-*`) and `docs/ai-cto/debt.md` (debt register, `DEBT-*`). Name the IDs
  each action touches. Blocked items live in `docs/ai-cto/blocked.md` with their unblock
  action, and stay there until their status changes.
- **Queue, don't choose.** Where options exist, list them in run order with action and
  reversibility. The user skips or punts items; act on the queue rather than stalling in
  Observe or Orient.
- **Anything needing the founder is a tile, not prose.** Each decision Dave must make is a
  loud block the founder can scan in one glance, with a **GO** or **NO GO** decision line:

  > **DECISION · DEC-NNN · <one-line question>**
  > **Action if GO:** <what runs>
  > **Action if NO GO:** <what stays>
  > **Decision needed:** **GO** or **NO GO**

  Tiles are never buried in a paragraph. One tile per decision, numbered `DEC-NNN`, and
  each is also recorded in `docs/ai-cto/blocked.md` until decided.
- **OODA is an ongoing goal (INIT-004).** Each cycle re-evaluates the rules: what failed,
  what has no check, and what tooling would catch it. A rule that lives only in prose is
  not a rule; it needs a check, a hook, or a file the next session reads. Raise the quality
  bar each cycle; never close the loop.
- **A null result gets new work.** When a session returns nothing useful, give it a concrete
  task in the same cycle rather than leaving it idle or repeating the prior prompt.
- **Commands assume a fresh terminal.** Every command given to the founder starts with
  the navigation to the repo, so it runs in a new CLI window with no prior `cd`:

  ```bash
  cd ~/localDNS
  <command>
  ```

  Put each command in its own fenced `bash` block, with the `cd` in the same block.
- **Successes are quiet.** One plain sentence with the evidence in parentheses. No
  celebration, no step-by-step recap.
- **Failures are loud.** Open with `FAILED:` or `BLOCKED:` in bold, quote the error, then
  give a numbered **Fix** recipe (one action per step, commands in `bash` fences). If the
  fix is unknown, give the next diagnostic command. Never report a failure without a recipe
  or a diagnostic.
- **No vague hedges** ("should work", "probably"). Name the check that would confirm it.
- No emoji. Headers no deeper than `###`.


---
