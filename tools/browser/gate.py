#!/usr/bin/env python3
"""Python port of .claude/hooks/gate.sh (PreToolUse(Bash): the commit gate).

Before any `git commit`, runs the repo's static checks; a failing check blocks the commit (exit 2, stderr goes
back to the model). Same failure policy as the original: a check that FAILS blocks, a hook that BREAKS lets the
commit through. Bypass: .claude/.gate-off.

Difference from the original, said out loud: in the browser there is no real OS, so check-matrix, check-bridge and
check-telepathy cannot run. When this is running under the browser shim, those are listed as "not run here" in the
block message and never counted as passed. On a real machine every check runs, as in the original.
"""
import json
import os
import re
import subprocess
import sys

try:
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or ".")
except OSError:
    sys.exit(0)
if os.path.exists(".claude/.gate-off"):
    sys.exit(0)
raw = sys.stdin.read()
if not raw.strip():
    sys.exit(0)
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)
if d.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (d.get("tool_input") or {}).get("command", "")
if not re.search(r"(^|[;&|\s])git\s+(-\S+\s+)*commit(\s|$)", cmd):
    sys.exit(0)

CHECKS = ["tools/check-docs.py", "tools/check-provenance.py", "tools/check-doctrine.py", "tools/sync-briefings.py",
          "tools/check-decisions.py", "tools/check-cardinal.py", "tools/check-matrix.py", "tools/check-stop-hook.py",
          "tools/check-registers.py", "tools/check-telepathy.py", "tools/check-statements.py",
          "tools/check-superfleet.py", "tools/check-bridge.py"]
NEEDS_REAL_OS = {"tools/check-matrix.py", "tools/check-telepathy.py", "tools/check-bridge.py"}
in_browser = bool(getattr(subprocess, "BROWSER_SHIM", False))

fails, skipped = "", []
for check in CHECKS:
    if not os.path.isfile(check):
        continue
    if in_browser and check in NEEDS_REAL_OS:
        skipped.append(check)
        continue
    try:
        r = subprocess.run(["python3", check], capture_output=True, text=True)
    except OSError as e:
        continue  # a hook that breaks lets the commit through
    if r.returncode != 0:
        tail = "\n".join(((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-20:])
        fails += "\n── %s ──\n%s" % (check, tail)

if not fails:
    sys.exit(0)

sys.stderr.write(
    "COMMIT GATE — blocked. A static check that decides mechanically says no.\n%s\n\n"
    "Fix the cause, not the gate. If this check is wrong, that is a finding about the\n"
    "check — change it in the same commit and say why. To bypass for a genuine WIP\n"
    "commit: touch .claude/.gate-off (and remember the invariant has no site while\n"
    "that file exists).\n" % fails)
if skipped:
    sys.stderr.write("\nNot run here (need a real OS, so not counted as passed): %s\n" % ", ".join(skipped))
sys.exit(2)
