# Factory run contract

A bounded, stoppable arc of work. It takes one entry at a time from
`docs/TECH-DEBT.md`, makes the fix on the work branch, runs the repo checks, and
records the result. It does not run without limits.

## Limits

See `.claude/factory/config.json`:

- `wall_clock_minutes`: 180 from the recorded start time.
- `max_iterations`: 10.
- `max_tool_calls`: 200.
- `kill_file`: `.claude/.factory-stop`. Creating it halts the run at the next check.

## Iteration procedure

Each iteration does these steps in order. A failed check ends the run.

1. **Check the stop conditions.** Halt if the kill file exists, the wall clock has
   passed its cap, the iteration count has reached `max_iterations`, or the
   tool-call count has reached `max_tool_calls`.
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

- It does not edit `.claude/settings.json` without a separate approval.
- It does not change the cloud environment.
- It does not push, open PRs, or subscribe to PR activity.
- It does not mark an entry closed on the strength of an unrun check. Checks it cannot
  run are reported as unverified.

## Status

The contract and limits are committed. The loop is not started. It starts when the
founder approves a run.
