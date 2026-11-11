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

## Iteration procedure, mapped to OODA

Before every step, not only at the start of an iteration, run the stop check in
step 1.

**Observe**

1. **Check the stop conditions.** Halt if the lease has expired or is `null`, the kill
   file exists, or a backstop cap has been reached. If a halt happens mid-fix, finish
   nothing new: leave the entry `open` and record where the run stopped.
2. **Read the register** and list the open entries, newest first. Skip entries past
   their `due` date and report them instead.

**Orient**

3. **Pick one entry** from the list. Mark an entry `blocked` (not `open`) if the fix
   needs the founder: a paste, a settings or environment change, a shell, or a whole-file
   push of a large file. Record the reason and move on to the next open entry. A run that
   only has blocked entries left ends. It does not spin on them.

**Decide**

4. **Choose the smallest fix** the entry's `fix` field describes. Keep to one entry. If
   the fix needs a file that can only be pushed whole and is large, mark the entry
   `blocked` instead.

**Act**

5. **Make the change and run the repo checks** on what changed: `tools/check-docs.py`,
   `tools/check-doctrine.py`, `tools/check-provenance.py`, `tools/check-debt.py`. Any
   failure halts the run. A check the run cannot execute is reported as unverified, not
   as passed.
6. **Record the result** in the register entry: `closed` only if the fix is verified,
   otherwise `open` or `blocked` with a note of what was checked.
7. **Stop for approval** before any push to a branch other than the work branch, any
   PR creation, or any settings or environment change. The run commits to the work branch
   and waits for approval on everything else.

## Retro

Each run ends with a short retro entry at the bottom of this file, under "Run log". It
records what was done, what was blocked and why, and one proposed change to this
procedure. The run does **not** apply its own proposed changes to this file. A proposal
waits for the founder to approve it, so the procedure cannot rewrite its own limits
unnoticed.

## What the factory does not do

- It does not extend or write its own lease.
- It does not edit `.claude/factory/config.json` or `.claude/settings.json` without a
  separate approval.
- It does not change the cloud environment.
- It does not push to other branches, open PRs, or subscribe to PR activity.
- It does not mark an entry closed on the strength of an unrun check.

## Status

The lease is active from `issued_at` to `expires_at` in `config.json`.

## Run log

### Run 1 (lease 2026-11-11T20:34:09Z to 23:34:09Z)
- **Done:** DEBT-007 closed (precedence header verified on the branch).
- **Blocked:** DEBT-008 needs a paste of the exact `CLAUDE.md` §C row, or approval for a
  whole-file push. DEBT-001 to DEBT-006 need a shell, settings, or environment change.
- **Checks:** none run. Bash is banned in this session, so the repo checks are unverified.
- **Proposed procedure change:** have the stop hook (or a small script) run the four check
  tools and write the result to the register, so a run with a shell can verify its own
  work. Awaiting founder approval.
