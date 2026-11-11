# Roadmap for Dave

Written 2026-11-11, 23:10 UTC. One page, plain English. If this page and another file
disagree about what you need to do, this page is the newer one.

## What happened

Two sessions built a set of tools for how Claude works in this repo. None of it touches the
t630, DNS, the VPN, or any customer document. All of it sits on one branch,
`decision-log-dec007`, in one draft pull request, PR #37. Nothing is on `main` yet, so a new
session does not have any of it until you say so.

## What was built, in four lines

- **Labels.** Every action Claude takes gets a one-line label saying what kind it is (looking, thinking, deciding, or changing something).
- **A stopwatch.** Every action is timed. Anything over 10 seconds is flagged on the spot.
- **Reply rules that enforce themselves.** A reply that skips the state word, hedges, or gives you a command that cannot run on your laptop is bounced before you see it.
- **Memory across restarts.** When a session is cut short or compacted, it reads `docs/ai-cto/checkpoint.md` and carries on.

Nothing is blocked by any of this today. It labels and measures; it does not stop Claude from doing anything.

## What you need to do

Six yes-or-no answers, in this order. The order matters only for the first one.

1. **DEC-011 · Merge PR #37 into `main`?** Do this one first: everything above is invisible to new sessions until it merges. Risk is low. All nine checks pass in the cloud and on your XPS, and nothing is blocked by the tools.
2. **DEC-013 · Shrink `CLAUDE.md`?** It is 69,000 characters and is loaded into every turn of every session, which costs money each time. A yes moves about 40% of it into files that are read only when needed. No rule is deleted.
3. **DEC-010 · Fewer decision tiles?** A yes means you get a tile only for something that truly needs you, not for every small choice.
4. **DEC-014 · Trim the cloud setup script?** A yes stops every new cloud session installing two packages it never uses, and makes it run all nine checks at start.
5. **DEC-012 · Turn on reminders ("warn" mode)?** A yes makes Claude remind itself to use the repo's own tools. Still nothing is blocked. Answer this after number 1 has merged.
6. **DEC-005 · Python environment files for the XPS?** This one needs two facts from your laptop first. Run this and paste the output:

```bash
cd ~/localDNS
echo "venv: $VIRTUAL_ENV"; ls ../venv
```

**How to answer:** one line is enough, for example `GO 011, GO 013, NO GO 012`. Anything you
leave out stays open and nothing happens to it.

## What Claude does without you

1. Done 2026-11-11: confirmed the labels also reach helper agents.
2. Checks, at the next compaction, that the session keeps the lease and decision list.
3. Carries out each decision above as soon as you answer it.

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

- Decisions and their evidence: `docs/ai-cto/blocked.md`
- Where the work stands: `docs/ai-cto/checkpoint.md`
- The finished work queue: `docs/ai-cto/handoff.md`
