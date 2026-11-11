---
name: orient
description: Cardinal skill Orient of the OODA loop. What does it mean, against our goals and debt? Its methods replace atomized skills; the tool-to-method map lives in .claude/cardinal-map.json.
---

# Orient

**Question this cardinal answers:** What does it mean, against our goals and debt?

Every tool call belongs to exactly one cardinal. Before a call, name it as
`orient.<method>`. The authoritative map is `.claude/cardinal-map.json`;
`tools/check-cardinal.py` fails if a tool sits in two cardinals or a method is empty.

## Methods

- `orient.ground` — read `docs/ai-cto/initiatives.md`, `docs/ai-cto/debt.md`, and
  `docs/ai-cto/blocked.md`; name the INIT and DEBT ids the work touches.
- `orient.reseed` — refresh the briefing: `/reseed`, `/refresh`.
- `orient.model` — which regimes a vote can be trusted in: `/diet`.
- `orient.explore` — read-only fan-out: Explore and Plan agents.

Rule: name every assumption as `Assume:`. Orient changes nothing on disk.
