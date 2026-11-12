# Race v3 quality: hand check (2026-11-12)

Method: a sample of claims from each of the four v3 runs (S1, S2, P1, P2), checked against the
code each cites. Claims were chosen from lanes R2, R6 and R8 because they are the most checkable.

Checked, TRUE as written:
- Cap test cannot fail (check-matrix.py:234; MATRIX_TEST_SLEEP popped at line 49). Stated in all four runs. TRUE.
- check-decisions.py: an empty log fails with "no DEC entries found" (lines 23-24). TRUE, and not in the
  docstring (lines 1-8). Stated in S2, P1 and P2.
- check-decisions.py line 15: the ENTRY regex accepts only the exact entry shape. TRUE (S1, P2).
- cardinal.py:48 map read in lookup() raises on a bad map. TRUE.
- cardinal.py:59 body["methods"] raises KeyError for a cardinal without methods. TRUE.
- cardinal.py:67 json.load(sys.stdin) sits inside the try opened at line 66. TRUE.
- cardinal.py:81 the second map read is outside any guard. TRUE.
- cardinal.py:89-90 lease.unlink() follows exists() without a guard. TRUE (S1, S2, P2).
- cardinal.py:157-158 the catch-all except Exception: pass. TRUE, and the common cause of the fail-open findings.

Checked, WRONG in detail:
- P2 R6 says the docstring "lists four failure conditions" and that the empty-log failure is the fourth.
  The docstring lists three (lines 4-7). The finding itself is correct; the count of the docstring's
  conditions is wrong.

Verdict on this sample: 12 of 13 claims are true as written. One is wrong in a detail, not in its
substance. No fabricated citation.

Agreement across the four runs: the same core findings appear in every run that covered their
lane. Cap test (R2), the cardinal.py fail-open paths (R8) and the empty-log check (R6) reappear in
each run's bullets. Agreement does not prove correctness, but the repetition is consistent, and
each repeated claim checked true.

Not checked: the other findings in these runs. The sample is 13 claims of about 165 across the four
runs, so the verdict covers the sample only.
