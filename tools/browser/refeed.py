#!/usr/bin/env python3
"""Python port of .claude/hooks/refeed.sh (SessionStart: the clear-and-refeed ritual).

The context text is NOT copied here: it is read from the heredoc in refeed.sh at run time, so the two
cannot drift. Only the sync half differs. The shell original runs git fetch and a fast-forward pull; this
port has no network, so it reports the snapshot it is running on and says it was not compared with origin.

Reads the SessionStart JSON on stdin. Standard library only.
Environment: CLAUDE_PROJECT_DIR (repo root), SNAPSHOT_REV (e.g. "71e6ccc 2026-11-12", used when git log is unavailable).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".")

try:
    payload = json.loads(sys.stdin.read() or "{}")
except json.JSONDecodeError:
    payload = {}
src = payload.get("source") or "startup"
if src not in ("startup", "clear"):
    sys.exit(0)


def git(*args):
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root)
        return r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        return ""


head = git("rev-parse", "HEAD")
sync_note = ("sync: snapshot %s; no network here, so not compared with origin" % head[:7]) if head else \
    "sync: no git state available here"
rev = git("log", "-1", "--format=%h %ci", "--", "CLAUDE.md") or os.environ.get("SNAPSHOT_REV") or "unknown"

try:
    text = (root / ".claude/hooks/refeed.sh").read_text(encoding="utf-8")
except OSError:
    sys.exit(0)
m = re.search(r"read -r -d '' ctx <<EOF \|\| true\n(.*?)\nEOF\n", text, re.S)
if not m:
    sys.exit(0)  # the shell hook changed shape: say nothing rather than inject something wrong
ctx = m.group(1)
for var, val in (("$sync_note", sync_note), ("$rev", rev), ("$src", src)):
    ctx = ctx.replace(var, val)

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
sys.exit(0)
