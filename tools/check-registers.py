#!/usr/bin/env python3
"""check-registers.py — gate for the AI-CTO registers (docs/ai-cto/initiatives.md, debt.md).

Fails if:
  * a DEBT-NNN or INIT-NNN heading does not end in a valid status,
  * an id appears twice, or the entries are not newest first (descending id),
  * a Blocked entry names neither a DEC id nor docs/ai-cto/blocked.md, so nobody can tell
    what would unblock it,
  * CLAUDE.md is over its byte budget (it is loaded on every turn, so growth is a cost).
Exit 0 when clean, 1 otherwise.
"""
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "docs/ai-cto"
BRIEFING_BUDGET = 60_000  # bytes; it was 69,153 before DEC-013
STATUSES = {"initiatives.md": ("INIT", {"Active", "Blocked", "Done", "Punted"}),
            "debt.md": ("DEBT", {"Open", "Blocked", "Done", "Punted"})}


def main() -> int:
    problems, total = [], 0
    for name, (prefix, allowed) in STATUSES.items():
        text = (DIR / name).read_text(encoding="utf-8")
        heads = list(re.finditer(r"^## (%s-(\d{3})) · (.*)$" % prefix, text, re.MULTILINE))
        if not heads:
            problems.append(f"{name}: no {prefix} entries found")
        nums = [int(h.group(2)) for h in heads]
        for n in sorted({n for n in nums if nums.count(n) > 1}):
            problems.append(f"{name}: {prefix}-{n:03d} appears more than once")
        if nums != sorted(nums, reverse=True):
            problems.append(f"{name}: entries are not newest first")
        for i, h in enumerate(heads):
            total += 1
            status = h.group(3).rsplit("·", 1)[-1].strip()
            if status not in allowed:
                problems.append(f"{name}: {h.group(1)} ends in {status!r}, not one of {sorted(allowed)}")
            body = text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            if status == "Blocked" and not re.search(r"DEC-\d{3}|blocked\.md", body):
                problems.append(f"{name}: {h.group(1)} is Blocked but names no DEC id and no blocked.md entry")
    # Rule inflation (DEBT-010): CLAUDE.md is loaded on every turn of every session, so it has a budget.
    briefing = len((DIR.parent.parent / "CLAUDE.md").read_bytes())
    if briefing > BRIEFING_BUDGET:
        problems.append(f"CLAUDE.md is {briefing:,} bytes, over its budget of {BRIEFING_BUDGET:,}. Move detail into "
                        "docs/ and leave one line, or give the rule a hook and shorten its prose. Do not raise the budget "
                        "without the founder.")
    for p in problems:
        print("FAIL", p)
    if not problems:
        print(f"ok   {total} register entries, each with a valid status, unique, newest first")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
