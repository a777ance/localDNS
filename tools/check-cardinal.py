#!/usr/bin/env python3
"""check-cardinal.py — gate for the cardinal alias map (.claude/cardinal-map.json).

Fails if: a cardinal is missing, a method is empty, a tool appears under two
cardinals, a cardinal has no SKILL.md, a SKILL.md omits one of its methods, a cardinal has no probe method, a mapped tool has neither
a quick probe nor a stated reason for lacking one, or a hook in
.claude/settings.json has no explicit timeout (the default is 600 seconds).
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
        if "probe" not in data[c]["methods"] or f'"{c}.probe"' not in matrix:
            problems.append(f"cardinal '{c}' has no probe method (1 + N lanes: the probe is lane 0 of every cardinal)")
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
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    for event, groups in settings.get("hooks", {}).items():
        for group in groups:
            for h in group.get("hooks", []):
                limit = h.get("timeout")
                if not isinstance(limit, int) or not 0 < limit <= 60:
                    problems.append(f"{event} hook has no timeout between 1 and 60 s (the default is 600 s): "
                                    f"{h.get('command', '')[-40:]}")
    probes = cfg.get("probes", {})
    for tool in sorted(mapped):
        entry = str(probes.get(tool, "")).strip()
        if not entry:
            problems.append(f"tool '{tool}' has no quick probe and no reason for lacking one (map key 'probes')")
        elif "matrix.py " in entry:
            method = entry.split("matrix.py ")[1].split()[0]
            if f'"{method}"' not in matrix:
                problems.append(f"probe for '{tool}' names {method}, which tools/matrix.py does not implement")
    for tool in sorted(set(probes) - mapped):
        problems.append(f"probe listed for '{tool}', which is not a mapped tool")
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
