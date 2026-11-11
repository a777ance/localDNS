#!/usr/bin/env python3
"""check-decisions.py — gate for the rule "every founder decision is in the DEC log".

Reads docs/ai-cto/blocked.md. Fails if:
  * a DEC-NNN entry has no status (OPEN, GO, NO GO, or MOOT),
  * a DEC id appears twice,
  * the entries are not newest first (descending id order).
Exit 0 when clean, 1 otherwise.
"""
import re
import sys
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "docs/ai-cto/blocked.md"
ENTRY = re.compile(r"^- \*\*DEC-(\d{3}) · (.*)$", re.MULTILINE)
STATUS = re.compile(r"·\s*(OPEN|GO|NO GO|MOOT)\b")


def main() -> int:
    text = LOG.read_text(encoding="utf-8")
    entries = [(int(m.group(1)), m.group(2)) for m in ENTRY.finditer(text)]
    problems = []
    if not entries:
        problems.append("no DEC entries found")
    seen = set()
    for num, body in entries:
        if num in seen:
            problems.append(f"DEC-{num:03d} appears more than once")
        seen.add(num)
        if not STATUS.search("· " + body):
            problems.append(f"DEC-{num:03d} has no status (OPEN, GO, NO GO, or MOOT)")
    nums = [n for n, _ in entries]
    if nums != sorted(nums, reverse=True):
        problems.append("DEC entries are not newest first")
    for p in problems:
        print("FAIL", p)
    if not problems:
        print(f"ok   {len(entries)} DEC entries, all with a status, newest first")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
