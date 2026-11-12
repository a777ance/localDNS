#!/usr/bin/env python3
"""racetrack_plan.py: plan a hybrid course over a fixed roadmap under a token budget.

A course is a list of stages. Each stage runs K agents in parallel (K=1 is sequential); its lanes
are split across those agents. Costs come from the measured v2 and v3 races (see RESULTS.md):

    agent tokens  ~ A + B * lanes      A = 87,000 fixed per agent, B = 10,000 per lane
    agent seconds ~ T0 + T * lanes     T0 = 20 s, T = 15 s per lane (a stage waits on its slowest agent)

Score = distance: the number of roadmap milestones finished in order before the budget runs out.
Ties go to the shorter wall time. Planning only: no model is called.

    python3 tools/racetrack_plan.py --budget 500000 --lanes 8
"""
import argparse
from functools import lru_cache

A, B = 87_000, 10_000
T0, T = 20, 15


def agent_cost(lanes):
    return A + B * lanes, T0 + T * lanes


def stage_cost(lanes, k):
    """Split `lanes` across k agents as evenly as possible. Returns (tokens, seconds)."""
    k = min(k, lanes)
    base, extra = divmod(lanes, k)
    tokens = secs = 0
    worst = 0
    for i in range(k):
        n = base + (1 if i < extra else 0)
        t, s = agent_cost(n)
        tokens += t
        worst = max(worst, s)
    return tokens, worst


def plan(lanes, budget, max_k=8):
    """Best course over the roadmap within `budget` tokens.

    Dynamic program over milestones. front[i] holds the Pareto set of courses that finish the first
    i milestones, each as (tokens, seconds, stages): no course in the set is both cheaper and faster
    than another. Returns (distance, seconds, stages) for the furthest milestone reached, at the
    shortest wall time among its courses. A stage is (first_lane, last_lane, agents), from 1.
    """
    front = {0: [(0, 0, ())]}
    for i in range(1, lanes + 1):
        cands = []
        for j in range(i):
            if j not in front:
                continue
            for k in range(1, min(max_k, i - j) + 1):
                t, s = stage_cost(i - j, k)
                for tok, sec, stages in front[j]:
                    if tok + t <= budget:
                        cands.append((tok + t, sec + s, stages + ((j + 1, i, min(k, i - j)),)))
        # Pareto filter on (tokens, seconds).
        cands.sort(key=lambda c: (c[0], c[1]))
        keep, best_sec = [], float("inf")
        for c in cands:
            if c[1] < best_sec:
                keep.append(c)
                best_sec = c[1]
        if keep:
            front[i] = keep
    dist = max(front)
    tok, sec, stages = min(front[dist], key=lambda c: c[1])
    return dist, sec, list(stages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, required=True, help="token budget for the course")
    ap.add_argument("--lanes", type=int, default=8, help="roadmap length in milestones (lanes)")
    a = ap.parse_args()
    d, secs, stages = plan(a.lanes, a.budget)
    print(f"budget {a.budget:,} tokens, roadmap {a.lanes} milestones: distance {d}, wall time {secs} s")
    for first, last, agents in stages:
        print(f"  stage: lanes {first}-{last} with {agents} agent{'s' if agents > 1 else ''}")


if __name__ == "__main__":
    main()
