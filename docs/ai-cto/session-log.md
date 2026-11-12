# Session log

The record for posterity: what each working session set out to do, what it shipped, what it
got wrong, and what it learned. Newest first. One entry per session, added at the end of the
session. Commit ids are on `main`.

---

## 2026-11-11 to 2026-11-12 · The Matrix goes live; look before the leap

**Set out to do:** work the 30-item queue left by the previous session (archived in
`docs/ai-cto/handoff-2026-11-11.md`): harden the Matrix tooling, measure the 10-second rule,
move the reply rules out of prose and into a hook.

**Shipped, in order:**

| What | Commit or PR |
| ---- | ------------ |
| Queue items Q-001 to Q-026: hook timeouts, bounded reads, backups and undo, call timing, five reply rules in the Stop hook, register gate, telepathy test | `743ef6d` to `a4298fe`, merged in PR #37 (`60a53d7`) |
| A plain-English roadmap for the founder; the cloud-only `cd` path fixed at its source | `996ce7f` |
| Subagent check: the hook line `cardinal: observe.read · agent: juror` seen live | `482d34d` |
| 20 leans on six decisions; `CLAUDE.md` cut from 69,153 to 59,123 bytes with nothing deleted | `fa94d93` |
| Decisions executed: DEC-010, DEC-011, DEC-013 (in part), DEC-014; DEC-012 by the founder's own hand | `60a53d7`, `67da1b6` |
| Rehearse every command handed to the founder; probe before egress | PR #39 (`cd6d9ff`) |
| Rehearsal copy fixed (stale remote); INIT-006 recorded | PR #40 (`b747788`) |
| A probe in every cardinal; lanes flagged without one; retrofit audit; scratchpad rule; laptop sync | PR #41 (`3514bda`) |
| This log, a fresh handoff, a current checkpoint, DEBT-011 closed | the commit that added this entry |

**After midnight, the branch model changed (DEC-015, DEC-016):**

- Three canonical branches: `main` emptied as intent cold storage, `leader` for all OODA and Matrix
  work, `outer` for the rest. `main-before-evacuation` is the frozen undo copy. Every other branch is
  marked superfluous in `docs/ai-cto/branches.md`; none was deleted.
- The founder's reference for it is the empty centre strategy, recorded with all six meanings as
  parables after he corrected a first write-up that had kept only three.
- `main` was emptied by the founder's own push (`646c709`). The command had been rehearsed against
  a stand-in of the remote and worked on his laptop on the first try, which is the first recipe of
  the session to do so for a change of that size.

**What went wrong, and the root cause of each:**

- **Three recipes failed on the founder's laptop.** One used the cloud container's path. One
  switched the gate to `warn` when no test had ever run with the live mode at `warn`. One
  left a merge as a step with nothing to paste. Root cause: nothing made a session run a
  command before handing it over (DEBT-012). Repair: `decide.rehearse`, enforced by the Stop hook.
- **The rehearsal tool's first run was itself wrong.** Its copy had a stale remote, so a
  rehearsed pull said "Already up to date" and exited 0. It was caught only because the output
  was read. Repair: the copy is a mirror, and the tool refuses to run on a wrong state.
- **A session tried to flip its own gate mode** and was refused by the permission system.
  The refusal is right. The mode is the founder's hand only.
- **The usage limit was reached** at 22:28 UTC on 2026-11-11 with peers running; the session ran on overage.

**What was learned:**

1. **Exit 0 is not evidence.** Read the output. Two of this session's faults passed their own exit code.
2. **A test that reads live configuration tests one configuration.** Pin the sandbox, then test each mode by name.
3. **A recipe step with nothing to paste gets skipped.** Either give the command or do the step.
4. **Gates are retroactive by nature; reply rules are not.** That gap is what retrofit closes.
5. **Rule inflation is real.** Every rule added to `CLAUDE.md` is paid for on every turn. A rule earns its line by having a hook or a check, and its prose shrinks to one line when it does.

**Measured:**

- Native tool calls timed live in the session: 95 by 00:40 UTC. Calls over 10 seconds: five. Four
  chained several ships or rehearsals in one shell call. The fifth was a single `act.ship` (11.7 s):
  nine gates in sequence plus the new push probe. Repair: `act.ship` now runs its gates side by side.
- Gates: nine, slowest about 4 seconds (`tools/check-matrix.py`), on the cloud container and on the founder's XPS.

**Left open:** the queue Q-031 to Q-039 in `docs/ai-cto/handoff.md`. Not seen live: a Stop-hook
bounce, a compaction using the `PreCompact` text, the laptop timer.
