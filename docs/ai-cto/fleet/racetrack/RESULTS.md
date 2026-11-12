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

## Race v3: sequential against parallel-8, two runs each (2026-11-12)

Same fixed task (TASK-v3.md), with notes kept out of the bullets. Every Count line matched its
bullets in all four runs, which the v2 races did not manage. Quality is NOT yet hand-checked for
these runs; the numbers below are volume and cost only.

| Run | Mode | Wall time | Subagent tokens | Findings | Citations | Bad citations | Findings per 1k tokens |
| --- | ---- | --------- | --------------- | -------- | --------- | ------------- | ---------------------- |
| S1 | sequential, 1 agent | 153 s | 176,885 | 37 | 40 | 0 | 0.21 |
| S2 | sequential, 1 agent | 120 s | 156,939 | 35 | 39 | 0 | 0.22 |
| P1 | parallel-8, 8 agents | not timed exactly (under about 2 min) | about 787,600 | 39 | 51 | 0 | 0.05 |
| P2 | parallel-8, 8 agents | not timed exactly | about 767,998 | 45 | 54 | 0 | 0.06 |

Sequential averages: 137 s, about 166,900 tokens, 36 findings, 0.215 findings per 1k tokens.
Parallel-8 averages: about 777,800 tokens, 42 findings, 0.054 findings per 1k tokens.

Read: parallel-8 cost about 4.7 times the tokens for about 17 percent more findings, so sequential is
about four times more efficient per finding. Wall time for parallel-8 was not timed exactly, so no
speed winner is claimed. Next: hand-check quality for each run before naming a quality winner.

## Course-30: the planner's single parallel stage, run for real (2026-11-12)

Roadmap: thirty milestones from repo files (`roadmap-30.json`), one fixed question each. The planner
chose one parallel stage of eight agents at a 2.4M-token budget (the $5 lease at the output-rate estimate).

- Milestones finished: 30 of 30. Each written as a defects report, not yet scored.
- Subagent tokens, summed from the eight agents: about 1,080,000 (about $2.27 at the output-rate estimate; $0.45 at the input rate).
- Wall time: the slowest agent took about 230 s (chunk 1, the largest files). The planner predicted 80 s; the model underpredicts when lanes read large files.
- Chained stages (a planner stage and a join stage): NOT run. The planner did not choose them, and the planner does not yet price them, so this course does not test chaining.
- Quality: not yet hand-checked. Several reports cite line numbers that may be stale; they need a sample check.
