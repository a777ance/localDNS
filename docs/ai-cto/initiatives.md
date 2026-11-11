# Initiatives and goals

What we are trying to achieve, and the line items that move each goal. Newest first. Read
at the Orient step of every briefing, so each reply can say which goal an action serves.
Update the status in the same commit as the work that changed it.

Status values: `Active` · `Blocked` (also in `blocked.md`) · `Queued` · `Done`.

---

## INIT-004 · OODA loop as an ongoing goal (RSI) · Active

- **Goal:** the OODA loop never finishes. Each cycle re-evaluates the rules, raises the quality bar, and adds tooling, so the recursive self-improvement loop keeps running.
- **Line items:**
  - Every cycle re-reads the reply-style rules and the Decide-Act gate, and records any rule that failed. Done in this cycle.
  - A null result from a session triggers new work for it, not silence. Recorded in `CLAUDE.md`.
  - Rule gatekeeping: a rule that only lives in prose is not a rule. Each one needs a check, a hook, or a file the next session reads. Queued.
  - Quality bar moves up each cycle: each new rule adds one measurable check. Queued.

## INIT-003 · Make session-to-session messaging work end to end · Active

- **Goal:** two Claude sessions exchange messages and each one wakes on arrival, without
  polling.
- **Line items:**
  - `send_message` wake between cloud sessions: **Done** (the "Gate test v2" ping and reply).
  - stdio mailbox (the telepathy stdio server (on branch `claude/youthful-hopper-7knhtn`)): **Done**, committed as `c1737f2`.
  - event-driven inbox watcher (the telepathy watcher (on branch `claude/youthful-hopper-7knhtn`)): **Done** on one machine, `fea6f36`.
  - two-session inbox test on one machine: **Queued**, see DEBT-005.
  - HTTP connector for cross-machine messaging: **Queued**, being built in another session.

## INIT-002 · Land the Briefing reply style everywhere it is read · Active

- **Goal:** every reply follows the Briefing style: lead state word, OODA structure,
  queued options, quiet successes, loud failures with fix recipes.
- **Line items:**
  - `.claude/output-styles/briefing.md`: **Done**, `582ddfd`.
  - `CLAUDE.md` reply-style section: **Done**, `582ddfd`.
  - Decide-Act Stop hook: **Done**, `795db26`. Live test in progress, see DEBT-001.
  - Blocked items persisted to disk: **Done**, `caf2491`.
  - App output-style picker: **Punted**, see DEBT-002.

## INIT-001 · Get PR #35 mergeable · Blocked

- **Goal:** PR #35 (`claude/youthful-hopper-7knhtn` → `main`) passes CI and can merge.
- **Line items:**
  - telepathy server, watcher, style, and hook commits on the branch: **Done**.
  - Cloudflare Workers Builds check green: **Punted**, see DEBT-004. Not part of the OODA loop project.
  - subscription noise from the other session stopped: **Blocked**, see DEBT-003.
