# Race 4 (parallel-8): hand review of quality (2026-11-12)

Method: sampled claims from every lane and checked each one against the code it cites. Sample of 12,
spread across all eight lanes. Not all 62 findings were checked.

Checked, all TRUE:
- R1 CLAUDE.md:50 "tiles" has no judgment gate: decide-act.py checks the tile's shape, not whether the question is the founder's. TRUE.
- R2 check-matrix.py:234 cap test cannot fail: MATRIX_TEST_SLEEP is removed from the sandbox env. TRUE (also confirmed in race 2 and by the v1 verdict).
- R3 check_plan 39-41, duplicate ids: the check exists. TRUE.
- R3 check_plan line 51: the Matrix-method test is a substring search over all of matrix.py, so a name in a comment passes. TRUE.
- R3 review line 79: compares with origin/leader...branch. TRUE.
- R4 loop-tick.md 8 vs 12: "Paused" and "Switched on" both stand. TRUE, a real contradiction.
- R5 prose-rules-audit row 15: the row says .gitignore covers .env only. FALSE in the row, and the agent caught it: .gitignore also covers *.env, secrets/ and vault/cleartext/. The finding stands.
- R6 check-decisions.py line 30: status matched anywhere after a middle dot, not in a status field. TRUE. Line 15: id pattern \d{3}. TRUE.
- R7 checkpoint.md:17: the lease line is a regex over handoff.md, not runtime state. TRUE.
- R8 cardinal.py:90: lease.unlink after an exists() check, unguarded. TRUE.
- R8 cardinal.py:138 and 149: a trail that is valid JSON but not a list raises TypeError, and the except catches only OSError and ValueError. TRUE.
- R8 cardinal.py:157-158: except Exception: pass. TRUE.

Verdict on this sample: 11 of 12 claims are true as written; the twelfth is wrong in the row but the
finding it supports is right. No fabricated citation. Every claim that could be checked held.

Quality by value, not count: the substantive findings are R8 (silent fail-open paths), R4 (the
contradictory status and the ratio rule's undefined "about the loop"), R2 (a test that cannot fail),
and R5 (ungated rules with no command). Many R3 and R6 findings say only that a docstring omits a
rule. That is true but low value, and it inflates the count.

Not checked: the remaining 50 findings. The count of 62 is a volume measure, not a quality measure.
