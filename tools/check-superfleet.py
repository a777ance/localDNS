#!/usr/bin/env python3
"""check-superfleet.py — gate for the superfleet plan (.claude/superfleet.json), DEC-020.

The plan describes ten scenarios of 1 + N lanes. It holds no instructions for any agent.

    python3 tools/check-superfleet.py                     check the plan (this is what the commit gate runs)
    python3 tools/check-superfleet.py --list              one line per scenario and lane
    python3 tools/check-superfleet.py --review S01 L2 BRANCH
                                                          check a lane's finished branch: did it change
                                                          anything outside its own write area?

The plan fails if: a scenario has no look-first step or fewer than two lanes; two lanes in the
whole plan have overlapping write areas; a write area is outside docs/ai-cto/fleet/; a lane has no
done-test; a look-first step names a Matrix method or check that does not exist.

The review fails if the branch changed any file outside the lane's write area, compared with the
branch `leader`. That is the one question a reviewer must not have to answer by eye.

Exit 0 when clean, 1 otherwise. Standard library only.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / ".claude/superfleet.json"
HOME = "docs/ai-cto/fleet/"


def load():
    return json.loads(PLAN.read_text(encoding="utf-8"))["scenarios"]


def check_plan(scenarios):
    problems, areas = [], []
    matrix = (ROOT / "tools/matrix.py").read_text(encoding="utf-8")
    ids = [s.get("id", "") for s in scenarios]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"scenario id {dup} appears more than once")
    for s in scenarios:
        sid = s.get("id", "?")
        if not re.fullmatch(r"S\d{2}", sid):
            problems.append(f"scenario id {sid!r} is not of the form S01")
        for key in ("title", "goal", "look_first", "review"):
            if not str(s.get(key, "")).strip():
                problems.append(f"{sid}: no {key}")
        first = str(s.get("look_first", ""))
        m = re.search(r"tools/matrix\.py (\w+\.\w+)", first)
        if m and f'"{m.group(1)}"' not in matrix:
            problems.append(f"{sid}: look-first names {m.group(1)}, which tools/matrix.py does not implement")
        c = re.search(r"(tools/check-[\w-]+\.py)", first)
        if c and not (ROOT / c.group(1)).exists():
            problems.append(f"{sid}: look-first names {c.group(1)}, which does not exist")
        if not m and not c:
            problems.append(f"{sid}: look-first is not a Matrix method or a check, so it cannot be run as lane 0")
        lanes = s.get("lanes", [])
        if len(lanes) < 2:
            problems.append(f"{sid}: fewer than two lanes; 1 + N needs N of at least 2 to be worth a fleet")
        for lane in lanes:
            lid, area = lane.get("id", "?"), str(lane.get("write_area", ""))
            if not str(lane.get("done_when", "")).strip() or not str(lane.get("covers", "")).strip():
                problems.append(f"{sid} {lid}: needs both 'covers' and 'done_when'")
            if not (area.startswith(HOME) and area.endswith("/") and ".." not in area):
                problems.append(f"{sid} {lid}: write area {area!r} is not a folder under {HOME}")
            areas.append((f"{sid} {lid}", area))
    for i, (a, pa) in enumerate(areas):
        for b, pb in areas[i + 1:]:
            if pa and pb and (pa.startswith(pb) or pb.startswith(pa)):
                problems.append(f"write areas overlap: {a} ({pa}) and {b} ({pb})")
    return problems, len(areas)


def review(scenarios, sid, lid, branch):
    lane = next((l for s in scenarios if s["id"] == sid for l in s["lanes"] if l["id"] == lid), None)
    if lane is None:
        return [f"no lane {sid} {lid} in the plan"], 0
    r = subprocess.run(["git", "diff", "--name-only", f"origin/leader...{branch}"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        return [f"cannot compare {branch} with origin/leader: {r.stderr.strip()[-160:]}"], 0
    changed = [f for f in r.stdout.splitlines() if f.strip()]
    outside = [f for f in changed if not f.startswith(lane["write_area"])]
    problems = [f"{branch} changed a file outside the write area of {sid} {lid}: {f}" for f in outside]
    if not changed:
        problems.append(f"{branch} changed nothing; the lane's done-test is: {lane['done_when']}")
    return problems, len(changed)


def main() -> int:
    scenarios = load()
    args = sys.argv[1:]
    if args[:1] == ["--list"]:
        for s in scenarios:
            print(f"{s['id']} · {s['title']} · look first: {s['look_first']}")
            for lane in s["lanes"]:
                print(f"    {lane['id']} · {lane['covers']}  →  {lane['write_area']}")
        return 0
    if args[:1] == ["--review"]:
        if len(args) != 4:
            print("FAIL usage: --review SCENARIO LANE BRANCH")
            return 1
        problems, n = review(scenarios, args[1], args[2], args[3])
        for p in problems:
            print("FAIL", p)
        if not problems:
            print(f"ok   {args[3]}: {n} file(s) changed, all inside the write area of {args[1]} {args[2]}")
        return 1 if problems else 0
    problems, n = check_plan(scenarios)
    for p in problems:
        print("FAIL", p)
    if not problems:
        print(f"ok   superfleet plan: {len(scenarios)} scenarios, {n} lanes, each with a look-first step and no overlapping write areas")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
