---
name: act
description: Cardinal skill Act of the OODA loop. What changed, and what is the evidence? Its methods replace atomized skills; the tool-to-method map lives in .claude/cardinal-map.json.
---

# Act

**Question this cardinal answers:** What changed, and what is the evidence?

Every tool call belongs to exactly one cardinal. Before a call, name it as
`act.<method>`. The authoritative map is `.claude/cardinal-map.json`;
`tools/check-cardinal.py` fails if a tool sits in two cardinals or a method is empty.

## Methods

- `act.probe` — lane 0 for Act: `ship FILE...` says what would be committed, runs the fast gates, and dry-runs the push; `edit PATH OLD` says whether an edit would apply exactly once. Neither changes anything.
- `act.write` — change files: Write, Edit, state-changing shell.
- `act.ship` — commit, push, open or merge a PR. Merge needs a founder GO.
- `act.message` — send to a session, a person, or a thread; includes the telepathy mailbox (`tools/telepathy/telepathy_mcp.py`: send, mark done).
- `act.recruit` — create, interrupt, or archive sessions; spawn worker agents.
- `act.schedule` — scheduled tasks and wake-ups.
- `act.watch` — subscribe or unsubscribe PR activity.
- `act.publish` — publish an Artifact.
- `act.configure` — settings, hooks, permissions: `/update-config`.
- `act.tidy` — clean up changed code after a fix lands: `/simplify`.
- `act.extend` — build and test new skills: `/skill-creator`.
- `act.resolve` — close a stall with its cause and the improvement made; logs to `docs/ai-cto/stalls.md`.
- `act.undo` — restore the latest backup of a path. `act.write` and `act.edit` back up to `.claude/.matrix-bak/` (git-ignored), never beside the file.

Loop: **slow**. Observe and Orient run on the fast loop; Decide and Act on the slow loop.

Rule: one Act line per Decided item, with its result. Successes quiet, failures loud with
a fix recipe. Irreversible or outward-facing acts need a founder GO first.
