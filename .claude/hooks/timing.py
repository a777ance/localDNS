#!/usr/bin/env python3
"""PostToolUse hook — measures how long each native tool call took.

The PreToolUse naming hook (cardinal.py) stamps a start time per tool call in
.claude/.matrix-starts/. This hook reads the stamp, appends one row to
.claude/.matrix-times (time, tool, cardinal, seconds; tab-separated), and, when the
call took more than 10 seconds, returns one line of context naming the breach.
Read the totals with: python3 tools/matrix.py observe.times

Fails open: any error prints nothing and exits 0. Standard library only.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
CAP = 10


def stamp_path(data: dict) -> Path:
    key = str(data.get("tool_use_id") or data.get("tool_name") or "unknown")
    return ROOT / ".claude/.matrix-starts" / re.sub(r"[^\w.-]", "_", key)[:120]


def main() -> int:
    try:
        data = json.load(sys.stdin)
        stamp = stamp_path(data)
        if not stamp.exists():
            return 0
        started, alias = stamp.read_text(encoding="utf-8").split("\t", 1)
        stamp.unlink()
        secs = time.time() - float(started)
        tool = data.get("tool_name", "unknown")
        with open(ROOT / ".claude/.matrix-times", "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\t{tool}\t{alias.strip()}\t{secs:.3f}\n")
        for old in stamp.parent.glob("*"):  # a denied or interrupted call leaves its stamp behind
            if time.time() - old.stat().st_mtime > 3600:
                old.unlink()
        if secs > CAP:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": (
                f"10-SECOND BREACH: native {tool} ({alias.strip()}) took {secs:.1f} s. A breach is a defect: "
                f"say what made it slow and bound or split the call. Totals: cd {ROOT} && "
                "python3 tools/matrix.py observe.times")}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
