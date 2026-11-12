# Racetrack results (v2, 2026-11-12)

Measured by tools/racetrack.py (citations, counts) and the agents' own usage reports. Subagent
tokens are the runtime's count, not dollars. Wall time is from launch to the last completion
notification, where recorded. Quality is NOT scored: only two v2 claims were spot-checked by hand
(none of race 2 to 4 yet), so findings per token measures output volume, not correctness.

| Race | Mode | Agents | Lanes | Subagent tokens | Bullets | Citations bad | Count defects | Findings per 1k tokens |
| ---- | ---- | ------ | ----- | --------------- | ------- | ------------- | ------------- | ---------------------- |
| 1 | sequential | 1 | 8 | 172,914 | 46 | 0 | 0 | 0.27 |
| 2 | batched-2 | 4 | 8 | about 426,700 | 38 | 0 | 1 (R7) | 0.09 |
| 3 | batched-4 | 2 | 8 | about 251,400 | 52 | 0 | 4 (R1 to R4) | 0.21 |
| 4 | parallel-8 | 8 | 8 | about 806,100 | 62 | 0 | 4 (R3, R5, R6, R7) | 0.08 |

Race 1 is the v2 sequential run. The earlier v1 four-lane sequential run is in `sequential/`, with
hand verdicts in `verdicts/sequential.md`; it is not in this table.

Wall time, where measured: race 1, 174.6 s (one agent). Race 2, about 67 s (four concurrent agents;
the slowest). Race 4, the slowest agent about 75 s; the launch-to-last-notification span was not timed.

Defect pattern: every race but race 1 wrote notes as bullets, so its Count line disagrees with its
bullets. The agents' reports said the counts matched in races 3 and 4; the scorer disagrees.

What the spot checks found (v1 sequential run and race 1 only): one false claim, one overstated,
one wrong count, four true of five checked. Races 2 to 4 are not yet spot-checked.
