# Verdicts on the sequential run (checked by hand against the code, 2026-11-12)

Scorer: `python3 tools/racetrack.py sequential`. Citations: 49, bad after resolver fix: 0.
Count mismatch: R3 claims 9, lists 10.

Claims spot-checked against the code (the scorer checks locations, not truth):

- R1, "decide-act.py has no LETTER key": TRUE (grep for "letter" finds nothing).
- R2, "line 189 asserts absence of EGRESS, and the Agent path never emits EGRESS": FALSE.
  Agent maps to `any` in `.claude/cardinal-map.json`; with no probe on record the hook emits
  EGRESS (tested in an empty sandbox). The test is a real check after a probe runs.
- R2, "the stall-closed check at line 232 is skipped silently by `if stalls:`": OVERSTATED.
  The `if stalls:` guards only the act.resolve call (line 228). Line 224 asserts one stall
  was recorded and fails if none, so the stall check cannot pass silently.
- R2, "MATRIX_TEST_SLEEP was removed in the environment at line 49, so the cap test is instant":
  TRUE. The cap-raise test cannot fail as written.
- R3, "fails a plan with duplicate scenario ids": TRUE (line 40 "appears more than once").

Result on spot checks: 4 true, 1 false, 1 overstated, 1 count error. Not all 33 claims were
checked; the rest are checked-by-location only.
