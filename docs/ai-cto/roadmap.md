# Roadmap for Dave

Written 2026-11-11, 23:10 UTC; updated 23:35 UTC after the merge. One page, plain English. If this page and another file
disagree about what you need to do, this page is the newer one.

## What happened

Two sessions built a set of tools for how Claude works in this repo. None of it touches the
t630, DNS, the VPN, or any customer document. All of it was merged into `main` on 2026-11-11 (PR #37), so every
new session now has it.

## What was built, in four lines

- **Labels.** Every action Claude takes gets a one-line label saying what kind it is (looking, thinking, deciding, or changing something).
- **A stopwatch.** Every action is timed. Anything over 10 seconds is flagged on the spot.
- **Reply rules that enforce themselves.** A reply that skips the state word, hedges, or gives you a command that cannot run on your laptop is bounced before you see it.
- **Memory across restarts.** When a session is cut short or compacted, it reads `docs/ai-cto/checkpoint.md` and carries on.

Nothing is blocked by any of this today. It labels and measures; it does not stop Claude from doing anything.

## What you need to do

You deferred the six decisions to the loop on 2026-11-11. Five are done. One still needs you.

| Decision | Result |
| -------- | ------ |
| DEC-014 · Trim the cloud setup script | Done. You approved the change; it applies to the next new cloud session. |
| DEC-013 · Shrink `CLAUDE.md` | Done in part: 69,153 to 59,123 characters, nothing deleted. Two large sections were left whole on purpose. |
| DEC-011 · Merge PR #37 | Done. Merged into `main` as `60a53d7`. |
| DEC-010 · Fewer decision tiles | Done. You now get a tile only for what cannot be undone, costs money, or touches the t630. |
| DEC-012 · Turn on reminders | Done. You set it yourself; `main` is at `67da1b6`. |
| DEC-005 · Python files for the XPS | **Needs you.** Two facts from your laptop. Command below. |

For DEC-005, run this and paste the output:

Not rehearsed: this command reads your laptop's own Python environment, which no cloud session can see.

```bash
cd ~/localDNS
echo "venv: $VIRTUAL_ENV"; ls ../venv
```

## What Claude does without you

1. Done 2026-11-11: confirmed the labels also reach helper agents.
2. Checks, at the next compaction, that the session keeps the lease and decision list.
3. Checks in the next new session that the merge and the trimmed setup script both took effect.

## What you can ignore

The vocabulary. If you see these, this is all they mean:

| Word | Meaning |
| ---- | ------- |
| the Matrix | the labels and the stopwatch together |
| cardinal | one of the four kinds of action: observe, orient, decide, act |
| lease | a time window in which Claude may work without asking |
| gate | a check that must pass before a commit |
| DEC / DEBT / INIT | a decision for you / a known flaw / a goal |
| stall | an action that ran past 10 seconds |

## Where the detail lives

- The 20 leans on these decisions: `docs/ai-cto/leans.md`
- Decisions and their evidence: `docs/ai-cto/blocked.md`
- Where the work stands: `docs/ai-cto/checkpoint.md`
- The next session's queue: `docs/ai-cto/handoff.md` (the finished one: `docs/ai-cto/handoff-2026-11-11.md`)
- The record of what happened and what was learned: `docs/ai-cto/session-log.md`
