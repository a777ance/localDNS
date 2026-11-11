#!/usr/bin/env python3
"""Loud check for docs/TECH-DEBT.md.

Fails (exit 1) when:
  - an entry is missing a required field,
  - an entry's status is not open|closed,
  - an open entry is past its due date,
  - the register has no entries at all (an empty register hides debt).

Run: python3 tools/check-debt.py [--today YYYY-MM-DD]
"""
import datetime
import pathlib
import re
import sys

REGISTER = pathlib.Path(__file__).resolve().parent.parent / "docs" / "TECH-DEBT.md"
REQUIRED = ["opened", "owner", "status", "due", "what", "why it is debt", "fix"]


def parse(text):
    entries = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        fields = {}
        for line in body.splitlines():
            m = re.match(r"- \*\*(.+?):\*\* ?(.*)", line)
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
        entries.append((head.strip(), fields))
    return entries


def main(argv):
    today = datetime.date.today()
    if "--today" in argv:
        today = datetime.date.fromisoformat(argv[argv.index("--today") + 1])
    entries = parse(REGISTER.read_text(encoding="utf-8"))
    problems = []
    if not entries:
        problems.append("register has no entries")
    for ident, f in entries:
        for key in REQUIRED:
            if not f.get(key):
                problems.append(f"{ident}: missing field '{key}'")
        status = f.get("status", "")
        if status not in ("open", "closed"):
            problems.append(f"{ident}: status must be open|closed, got '{status}'")
        if status == "open" and f.get("due"):
            try:
                due = datetime.date.fromisoformat(f["due"])
            except ValueError:
                problems.append(f"{ident}: due '{f['due']}' is not YYYY-MM-DD")
                continue
            if due < today:
                problems.append(f"{ident}: OVERDUE since {due} ({f.get('what', '')[:60]})")
    open_count = sum(1 for _, f in entries if f.get("status") == "open")
    print(f"tech debt: {len(entries)} entries, {open_count} open")
    for p in problems:
        print(f"!! {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
