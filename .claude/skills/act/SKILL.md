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

- `act.write` — change files: Write, Edit, state-changing shell.
- `act.ship` — commit, push, open or merge a PR. Merge needs a founder GO.
- `act.message` — send to a session, a person, or a thread.
- `act.recruit` — create, interrupt, or archive sessions; spawn worker agents.
- `act.schedule` — scheduled tasks and wake-ups.
- `act.watch` — subscribe or unsubscribe PR activity.
- `act.publish` — publish an Artifact.

Rule: one Act line per Decided item, with its result. Successes quiet, failures loud with
a fix recipe. Irreversible or outward-facing acts need a founder GO first.
