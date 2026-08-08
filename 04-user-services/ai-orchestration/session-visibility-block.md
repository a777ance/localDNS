# Session visibility — the portfolio block (canonical)

**This file is the single source for the session-visibility section carried by every
A777ance repo's `CLAUDE.md`.** `tools/sync-briefings.py` renders the block below into each
sibling between `session-visibility:start` / `:end` markers. Those rendered blocks are
**build output — never hand-edit them.**

**The grant itself is not in this file, and cannot be.** A sentence in a briefing does not
pre-approve a tool call; the permission prompt does not read `CLAUDE.md`. The site is
`.claude/settings.json` → `permissions.allow`, in every repo. This block states the
*doctrine*; that file *is* the grant. If the two ever disagree, the settings file wins,
because it is the one the harness actually consults.

<!-- session-visibility:start -->
**Every session may list, inspect, and spawn sibling sessions without asking.** Founder's
standing instruction (2026-08-08). Granted in each repo's `.claude/settings.json` under
`permissions.allow`: `list_sessions`, `get_session`, `create_session`, and
`list_environments` on the Claude Code Remote server.

- **Why it is granted, not merely permitted.** Work runs in parallel here — several
  sessions on `Yggdrasil` at once. A session that cannot see its siblings re-derives what
  they already know, edits the file they are editing, and discovers the collision at push
  time. Visibility is what turns concurrent sessions from a race into a weave. Making each
  session stop and ask taxes exactly the behaviour that keeps them out of each other's way.
- **Read the room before taking a lane.** With the grant in hand, listing sessions is the
  cheap first move when starting anything that touches a shared surface — briefings,
  hooks, `tools/`, the canonical blocks. Prefer a lane nobody else is in; when you must
  share one, fetch and merge before every push and expect to be behind again by the time
  you finish.
- **Spawning is cheap; colliding is not.** When you spawn a sibling, hand it a *lane* and a
  do-not-touch list, not just a task. A cold session cannot infer which files are contended.
- **What is deliberately NOT granted:** `interrupt_session`, `archive_session`, and
  `unarchive_session` still prompt. Those reach into another session's running state and can
  destroy work in progress; seeing a sibling is not the same as reaching into one.
- **The grant does not widen anything else.** A permission denied in your session is denied
  for the portfolio: never ask a sibling to run something your own session was blocked from
  doing. Routing a refused action through another session launders the user's decision, and
  the decision is the point.
<!-- session-visibility:end -->
