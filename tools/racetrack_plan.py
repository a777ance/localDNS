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

    Returns (distance, seconds, stages). A stage is (first_lane, last_lane, agents), lanes counted
    from 1. Distance is the milestones finished in order before the budget runs out; a course is
    never cut mid-stage. Ties on distance go to the shorter wall time.
    """
    best = {"dist": 0, "secs": 0, "stages": []}

    def consider(dist, secs, stages):
        if (dist, -secs) > (best["dist"], -best["secs"]):
            best.update(dist=dist, secs=secs, stages=list(stages))

    def walk(start, spent, secs, stages):
        consider(start, secs, stages)
        if start == lanes:
            return
        for end in range(start + 1, lanes + 1):
            for k in range(1, min(max_k, end - start) + 1):
                tokens, s = stage_cost(end - start, k)
                if spent + tokens > budget:
                    continue
                walk(end, spent + tokens, secs + s, stages + [(start + 1, end, min(k, end - start))])

    walk(0, 0, 0, [])
    return best["dist"], best["secs"], best["stages"]


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
