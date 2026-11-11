---
name: decide
description: Cardinal skill Decide of the OODA loop. What is the queue, and what needs the founder? Its methods replace atomized skills; the tool-to-method map lives in .claude/cardinal-map.json.
---

# Decide

**Question this cardinal answers:** What is the queue, and what needs the founder?

Every tool call belongs to exactly one cardinal. Before a call, name it as
`decide.<method>`. The authoritative map is `.claude/cardinal-map.json`;
`tools/check-cardinal.py` fails if a tool sits in two cardinals or a method is empty.

## Methods

- `decide.queue` — the numbered queue, in run order; never choose between options.
- `decide.tile` — a founder decision as a GO / NO GO tile (AskUserQuestion), logged as DEC-NNN.
- `decide.vote` — a jury verdict: `/cardio`, `/strength`, `/workout`, juror agents.
- `decide.gate` — the static checks under `tools/` that say yes or no mechanically.
- `decide.open` — the founder decisions still OPEN in the decision log.

Loop: **slow**. Observe and Orient run on the fast loop; Decide and Act on the slow loop.

Rule: tiles are only for decisions the founder alone can make. Everything else in the
queue runs without asking.
