# Factory roadmap

What the factory can work on, in order, and what each item needs. Each item is tagged
with its OODA stage and whether it is runnable without the founder. Items marked
**founder** need a paste, a settings or environment change, or a shell before they can
close. The run never closes an item it could not verify.

## Runnable now (branch-only, verifiable by reading)

1. **DEBT-002: confirm `jury-claude/` exists** (Observe). List the directory on the
   branch and confirm the files named in CLAUDE.md §C exist. Close the entry if they do,
   and say which were checked.
2. **DEBT-003: draft the stop-hook file-list proposal** (Orient, Decide). Read
   `.claude/hooks/momentum.sh` and write a proposal under `docs/factory/proposals/` for
   printing the untracked-file list the hook reacts to. Apply it only with approval.
3. **Proposal: run-verification script** (Decide). Draft a script that runs the four
   repo checks and writes the result to the register. It is written, not run, and is
   marked unverified until a shell runs it.

## Blocked on the founder

- **DEBT-008** is done as of this push: the §C row now says "a bare run reports drift".
  Note: an earlier proposal said section 4 also repeats the phrase. It doesn't; only
  the §C row does.
- **DEBT-005** needs a shell: `chmod +x .claude/hooks/alias.sh`, then confirm `rm -rf`
  is blocked and `git status` runs.
- **DEBT-004** (`unbound-checkconf`) needs a shell and a setup-script change.
- **DEBT-006** (environment network) needs an approval in the environment UI.
- **DEBT-001** (what created the PR subscription) needs the founder's knowledge of the
  session that did it.

## Retro hook

Each run appends a "Run log" entry to `docs/factory/README.md` under the lease that
produced it. Proposed procedure changes are written there and wait for approval.
