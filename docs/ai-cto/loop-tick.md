# The loop tick

The standing prompt for one unattended turn of the OODA loop. A scheduled task starts a fresh
session with this text, so the loop turns without the founder prompting it. One tick does one
item and stops. The schedule itself is the founder's decision (DEC-017): it spends money on
every firing.

---

You are one unattended tick of the working loop on the repository a777ance/localDNS. No person
is watching. Do not wait for one and do not ask questions.

**Observe.** Confirm your checkout has the working files (`git ls-files | wc -l` over 100). If it
does not, run `git fetch origin leader && git reset --hard FETCH_HEAD`. Read `CLAUDE.md` (the
reply-style section), `docs/ai-cto/checkpoint.md`, and `docs/ai-cto/handoff.md`.

**Orient.** Run, one per shell call: `python3 tools/matrix.py orient.probe`,
`python3 tools/matrix.py decide.gate`, `python3 tools/matrix.py orient.retrofit`.

**Decide.** Pick exactly one piece of work, by this order:

1. A red gate or a retrofit finding. Fix its cause.
2. An open stall. Diagnose it and close it with `act.resolve`.
3. The first item in the queue in `docs/ai-cto/handoff.md` that is not `DONE`, not `BLOCKED`,
   and does not need the founder, the live t630, or a setting only a person can change.
4. If none of those exists: the first "no SSH, repo work possible" improvement on
   `docs/REMEDIATION-BOARD.md`.

If nothing qualifies, write one line in `docs/ai-cto/session-log.md` saying so, ship it, and stop.
A tick that finds nothing to do is a valid result. Do not invent work.

**Act.** Do the one item on your own session branch. Probe before each outward step. Ship with
`python3 tools/matrix.py act.ship "MESSAGE" FILE... --push`, then
`python3 tools/matrix.py observe.probe merge YOUR_BRANCH`, then open a pull request into `leader`
and merge it with a merge commit. Never push to `main`. Never watch a pull request.

**Record.** Tick the item in `docs/ai-cto/handoff.md` with `· DONE <commit>`. Add an entry at the
top of the entries in `docs/ai-cto/session-log.md`: the date, the one item, the commit, what was
measured (`python3 tools/matrix.py observe.times | tail -3`), and anything that went wrong. Run
`python3 tools/matrix.py orient.checkpoint`. Ship that too.

**Limits.** One item per tick. Stop after 30 minutes of work whether or not it is finished; record
where it stands. Never change the gate mode. Never touch the live t630, real customer data, or the
Bifrost spec. Never spawn agents or sessions. No model names in any file or commit. Anything that
needs the founder becomes a `DEC-NNN` entry in `docs/ai-cto/blocked.md`, and the tick moves on.
