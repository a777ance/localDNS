#!/usr/bin/env python3
"""Python port of .claude/hooks/momentum.sh (Stop hook: guarded auto-continue).

Same contract as the shell original, for places with no bash (the in-browser explorer):
inert unless .claude/.momentum-on exists; hard cap MAX; yields when HEAD has not moved since the
last continue; disarms itself on every stop condition; fails safe. Reads and writes the same files.
Standard library only.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or ".")
except OSError:
    sys.exit(0)

ARM = Path(".claude/.momentum-on")
STATE = Path(".claude/.momentum-state")
MAX = 10

if not ARM.is_file():
    sys.exit(0)


def allow_stop():
    for p in (ARM, STATE):
        try:
            p.unlink()
        except OSError:
            pass
    sys.exit(0)


count, lastsha = 0, ""
try:
    if STATE.is_file():
        first = (STATE.read_text(encoding="utf-8").splitlines() or [""])[0].split()
        count = int(first[0]) if first and first[0].isdigit() else 0
        lastsha = first[1] if len(first) > 1 else ""
except (OSError, ValueError):
    count, lastsha = 0, ""

try:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    head = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "none"
except OSError:
    head = "none"

if count >= MAX:
    allow_stop()
if lastsha and head == lastsha:
    allow_stop()

count += 1
STATE.write_text("%d %s\n" % (count, head), encoding="utf-8")

reason = ("AUTO-MOMENTUM %d/%d: keep going — do the next unblocked item in docs/ai-cto/context.md section "
          "\"Default next actions\", ship it as a verified, pushed change, then continue. STOP the loop YOURSELF the "
          "instant you are blocked, awaiting the founder, or the queue is empty, by running: rm -f %s. Anything "
          "irreversible or outward-facing (deletes, force-pushes, external sends, real customer data) still needs a "
          "confirm first." % (count, MAX, ARM))
print(json.dumps({"decision": "block", "reason": reason}, separators=(",", ":")))
sys.exit(0)
