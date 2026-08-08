# Session tooling — the portfolio block (canonical)

**This file is the single source for the session-tooling section carried by every A777ance
repo's `CLAUDE.md`.** `tools/sync-briefings.py` renders the block below into each sibling
between `session-visibility:start` / `:end` markers. Those rendered blocks are **build
output — never hand-edit them.** (The marker keeps its original name so existing renders
stay addressable; the *heading* widened when triggers and repos were added.)

**The grant itself is not in this file, and cannot be.** A sentence in a briefing does not
pre-approve a tool call; the permission prompt does not read `CLAUDE.md`. The site is
`.claude/settings.json` → `permissions.allow`, in every repo. This block states the
*doctrine*; that file *is* the grant, and `tools/sync-briefings.py` fails the commit if the
two disagree — so a briefing cannot promise access the settings file does not carry.

<!-- session-visibility:start -->
**Every session may see its siblings, schedule its own follow-ups, and attach the repos it
needs — without asking.** Founder's standing instruction (2026-08-08). Granted in each
repo's `.claude/settings.json` under `permissions.allow`, on the Claude Code Remote server:

| Granted | Why it is safe to grant |
| --- | --- |
| `list_sessions` · `get_session` · `create_session` · `list_environments` | Seeing and spawning. Work here runs in parallel; a session blind to its siblings edits the file they are editing and finds out at push time. |
| `list_triggers` · `create_trigger` · `update_trigger` · `send_later` | Scheduling its own follow-up. A session that cannot set a reminder either polls (wasteful) or drops the thread (worse). |
| `add_repo` · `list_repos` · `register_repo_root` | Attaching what the task needs. Scoped to repos the account already has — it widens the working set, never the account. |
| `set_session_title` · `set_session_tags` | Self-labelling, so a listing is legible to the next weaver. |

- **Deliberately NOT granted:** `delete_trigger`, `fire_trigger`, `interrupt_session`,
  `archive_session`, `unarchive_session`. Each either destroys something or fires an effect
  *now*. Creating a routine is additive and visible; deleting the founder's routine, or
  firing one early, is neither. Seeing a sibling is not reaching into one.
- **Triggers are the one grant that acts when nobody is watching.** Everything else here
  happens in-turn, in view. A scheduled routine fires later, and a fresh-session trigger
  runs with no one reading over its shoulder — so it inherits the Bifrost one-way door
  rather than escaping it: **a trigger may prepare, report, and check; it may not be the
  thing that performs an irreversible outward-facing action.** Publish, deploy, send, delete,
  merge to `main` — those wait for the founder at the `*` gate, whatever the cron says. Name
  routines so a listing reads plainly, and prefer one that reports back over one that acts.
- **Read the room before taking a lane.** Listing sessions is the cheap first move before
  touching a shared surface — briefings, hooks, `tools/`, the canonical blocks. Prefer an
  empty lane; when you must share one, fetch and merge before every push.
- **Spawning is cheap; colliding is not.** Hand a spawned sibling a *lane* and a
  do-not-touch list, not just a task. A cold session cannot infer which files are contended.
- **The grant widens nothing else.** A permission denied in your session is denied for the
  portfolio: never route a blocked action through a sibling, and never schedule a trigger to
  do later what you were refused now. Both launder the founder's decision, and the decision
  is the point.
<!-- session-visibility:end -->
