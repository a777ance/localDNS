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
    cfg = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))
    data = cfg["cardinals"]
    problems, owner, count = [], {}, 0
    if cfg.get("mode") not in ("name", "warn", "enforce"):
        problems.append(f"mode must be name, warn, or enforce, not {cfg.get('mode')!r}")
    matrix = (ROOT / "tools/matrix.py").read_text(encoding="utf-8")
    mapped = {t for c in data.values() for ts in c["methods"].values() for t in ts}
    for tool, target in cfg.get("repoint", {}).items():
        method = target.split("matrix.py ")[-1].split()[0]
        if f'"{method}"' not in matrix:
            problems.append(f"repoint for {tool} names {method}, which tools/matrix.py does not implement")
        if tool not in mapped:
            problems.append(f"repointed tool {tool} is not in any cardinal")
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
