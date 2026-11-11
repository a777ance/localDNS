# Factory run contract

A stoppable arc of work. It takes one entry at a time from `docs/TECH-DEBT.md`,
makes the fix on the work branch, runs the repo checks, and records the result. The
loop has no fixed length. A **lease** bounds it.

## The lease

See `.claude/factory/config.json`, field `lease`:

- `expires_at`: the run halts when the wall clock passes this time. `null` means no
  active lease, and the factory refuses to start.
- `renewed_by`: who last wrote the lease. Only the founder writes it.
- Renewal means the founder writes a new `expires_at`. The agent never sets or extends
  it.

## Backstops

`max_iterations` (10) and `max_tool_calls` (200) are secondary guards against a run
that is stuck on one failure. They do not replace the lease.

## Kill file

Creating `.claude/.factory-stop` halts the run at the next check.

## Iteration procedure

Before every step, not only at the start of an iteration:

1. **Check the stop conditions.** Halt if the lease has expired or is `null`, the kill
   file exists, or a backstop cap has been reached. If a halt happens mid-fix, finish
   nothing new: leave the entry `open` and record where the run stopped.
2. **Pick one open entry** from the register, newest first. Skip entries past their
   `due` date and report them instead.
3. **Make the smallest fix** the entry's `fix` field describes. Keep to one entry.
4. **Run the repo checks** on what changed: `tools/check-docs.py`,
   `tools/check-doctrine.py`, `tools/check-provenance.py`, `tools/check-debt.py`.
   Any failure halts the run.
5. **Record the result** in the register entry: `closed` only if the fix is verified,
   otherwise leave it `open` with a note of what was checked.
6. **Stop for approval** before any push or PR creation. The run commits locally and
   waits.

## What the factory does not do

- It does not extend or write its own lease.
- It does not edit `.claude/settings.json` without a separate approval.
- It does not change the cloud environment.
- It does not push, open PRs, or subscribe to PR activity.
- It does not mark an entry closed on the strength of an unrun check. Checks it cannot
  run are reported as unverified.

## Status

The lease is committed with `expires_at` unset, so the factory will not start. The
founder sets `issued_at` and `expires_at` to start a run.
