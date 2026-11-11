#!/usr/bin/env python3
"""check-cardinal.py — gate for the cardinal alias map (.claude/cardinal-map.json).

Fails if: a cardinal is missing, a method is empty, a tool appears under two
cardinals, a cardinal has no SKILL.md, or a SKILL.md omits one of its methods.
Exit 0 when clean, 1 otherwise.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDINALS = ("observe", "orient", "decide", "act")


def main() -> int:
    data = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))["cardinals"]
    problems, owner, count = [], {}, 0
    for c in CARDINALS:
        if c not in data:
            problems.append(f"cardinal '{c}' missing from the map")
            continue
        skill = ROOT / f".claude/skills/{c}/SKILL.md"
        text = skill.read_text(encoding="utf-8") if skill.exists() else ""
        if not text:
            problems.append(f"no skill file for '{c}'")
        for method, tools in data[c]["methods"].items():
            if not tools:
                problems.append(f"{c}.{method} has no tools")
            if text and f"`{c}.{method}`" not in text:
                problems.append(f"{c}.{method} is not documented in its SKILL.md")
            for t in tools:
                count += 1
                if t in owner and owner[t] != c:
                    problems.append(f"tool '{t}' is in both '{owner[t]}' and '{c}'")
                owner[t] = c
    extra = set(data) - set(CARDINALS)
    if extra:
        problems.append(f"unknown cardinals: {sorted(extra)}")
    for p in problems:
        print("FAIL", p)
    if not problems:
        print(f"ok   {count} tool aliases across {len(CARDINALS)} cardinals, each in exactly one")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
