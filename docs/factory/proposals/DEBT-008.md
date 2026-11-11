# DEBT-008 proposal: correct the sync-briefings row in CLAUDE.md section C

## Problem

CLAUDE.md section C describes `tools/sync-briefings.py` with `--check`. The script
rejects that flag. A bare run reports drift.

## Replacement text

In the section C table, replace the `tools/sync-briefings.py` row's description
fragment:

- **Find:** `bare/`--check` reports drift, `--write` fixes it`
- **Replace with:** `a bare run reports drift, `--write` fixes it`

The row's Repo path, System path, and Reload columns are unchanged.

Section 4 (Further reading) repeats the phrase "bare/`--check` reports drift". Apply
the same replacement there so the two places agree.

## Verification

Run `python3 tools/sync-briefings.py` (bare) and confirm it runs without the `--check`
flag. A run with the flag is expected to fail with an unrecognized-argument error.

## Approval

Not applied. Apply by paste, or approve the whole-file push of CLAUDE.md.
