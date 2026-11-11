---
name: observe
description: Cardinal skill Observe of the OODA loop. What is true right now? Its methods replace atomized skills; the tool-to-method map lives in .claude/cardinal-map.json.
---

# Observe

**Question this cardinal answers:** What is true right now?

Every tool call belongs to exactly one cardinal. Before a call, name it as
`observe.<method>`. The authoritative map is `.claude/cardinal-map.json`;
`tools/check-cardinal.py` fails if a tool sits in two cardinals or a method is empty.

## Methods

- `observe.read` — files and read-only shell: Read, Glob, Grep.
- `observe.listen` — events that arrive: ReadNotifications, Monitor, session events.
- `observe.survey` — the fleet: sessions, environments, scheduled tasks, repos.
- `observe.inspect` — GitHub state: PRs, check runs, commits, logs.
- `observe.fetch` — outside facts: web, docs, tool and plugin search.
- `observe.measure` — measured p-hat: `/form`, `/workout.calibrate`.

Rule: report only what was seen, with the evidence in parentheses. Never poll; listen.
