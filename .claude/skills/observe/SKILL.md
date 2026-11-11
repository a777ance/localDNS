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
- `observe.listen` — events that arrive: ReadNotifications, Monitor, session events, and the telepathy mailbox (`tools/telepathy/watch.py`, inbox, read).
- `observe.survey` — the fleet: sessions, environments, scheduled tasks, repos.
- `observe.inspect` — GitHub state: PRs, check runs, commits, logs.
- `observe.fetch` — outside facts: web, docs, tool and plugin search.
- `observe.measure` — measured p-hat: `/form`, `/workout.calibrate`.
- `observe.verify` — launch the app and see the change working: `/run`.
- `observe.research` — multi-source research into a report: `/deep-research`.
- `observe.status` — branch, changed files, Matrix mode, leases, and open stalls in one call.
- `observe.probe` — dry-run before egress: `push` dry-runs the push of this branch; `merge BRANCH` reports ahead, behind, and conflicts against the base. The naming hook flags a push or merge call with no passing probe in the last 10 minutes. `act.ship` probes its own push before it commits.
- `observe.log` — the Matrix watching itself: calls per cardinal and method from `.claude/.matrix-log`, and the slowest call. The log rotates at 2,000 lines.
- `observe.times` — measured duration of every native tool call (count, median, worst, each call over 10 s); `--debt` drafts a `DEBT-NNN` block per breaching tool.

Loop: **fast**. Observe and Orient run on the fast loop; Decide and Act on the slow loop.

Rule: report only what was seen, with the evidence in parentheses. Never poll; listen.
