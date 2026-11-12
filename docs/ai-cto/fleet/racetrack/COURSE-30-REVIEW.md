# Course-30: hand check of the reports (2026-11-12)

Method: one defect from each of the twenty-one reports that open with a bullet, checked against the
line it cites; plus the claims below. The reports M09 to M12 and M25 to M27 open with a bold heading
rather than a bullet, and were NOT sampled.

Checked, TRUE as written (11):
- M01: the eight rule-level [hook] tags are at CLAUDE.md lines 36, 41, 43, 53, 55, 63, 64 and 72. TRUE.
- M03: matrix.py line 353 writes the "any" probe unconditionally, including FAILED runs. TRUE.
- M04: line 83 with an empty write area (startswith("")) flags nothing. TRUE.
- M14: check-stop-hook.py line 78 returns "" on empty stdout, which reads as allow. TRUE.
- M15: the GIGABYTES pattern does not match "9.5GB" (no word boundary between a digit and GB). TRUE.
- M21: timing.py line 24 falls back to the tool name for the stamp key. TRUE.
- M22: gate.sh line 18 says "three static checks". TRUE.
- M23: resume.py line 25 reads the checkpoint with no guard. TRUE for line 25; the swallow at lines 36-37 was NOT checked.
- M24: precompact.py line 19 has timeout=4 and no guard. TRUE for line 19; the handler at 48-49 was NOT checked.
- M28: branches.md line 77 is the heading "Every other branch is superfluous". TRUE.
- M05 and M06 and M07 (earlier sample, same races): TRUE.

Verdict: 11 of 11 sampled claims are true as written. No fabricated citation. Confidence is high
for the sample and moderate for the rest, which were not sampled.

## So what?

1. The course works mechanically. Thirty milestones ran in one parallel stage of eight agents for
   about 1.08M subagent tokens (about $2.27 at the output-rate estimate, inside the $5 lease), in about
   230 seconds of slowest-agent wall time. The planner predicted 80 seconds, so it underpredicts.
2. The output is real. The reports name defects that matter: fail-open hooks that let a call run
   unchecked (cardinal.py, timing.py, resume.py, precompact.py), gates that pass when they should fail
   (check-superfleet, check-telepathy, check-statements), and instructions that contradict each other
   (loop-tick status, checkpoint counts, branches.md). The reports' own counts add to at least 165
   defects; the remainder are unstated.
3. The so-what for the product: the repo's checks are weaker than their docstrings claim. That is a
   quality problem in the repo, not in the racetrack. It is the most valuable finding of this course.
4. The so-what for the racetrack: volume is cheap, but distance is saturated. Every course reached
   30 of 30 at this budget, so the $5 lease never decided anything. Chaining was not tested, and the
   planner's time model needs refitting before its ranking can be trusted.
5. Next: fix the fail-open paths first (highest impact per line changed), then price the chained
   stages in the planner and rerun the course to test them.
