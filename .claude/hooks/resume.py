#!/usr/bin/env python3
"""SessionStart(compact) hook — wake the session back into its work after a compaction.

A compaction keeps a summary and drops the detail. This hook puts the resume point back
in front of the session the moment the compaction finishes: the checkpoint file, the
Matrix status, and the open founder decisions. Its stdout becomes session context.
Fails open: any error prints nothing and exits 0. Standard library only.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def run(*method):
    r = subprocess.run([sys.executable, str(ROOT / "tools/matrix.py"), *method],
                       capture_output=True, text=True, cwd=ROOT, timeout=10)
    return r.stdout.strip()


def main() -> int:
    try:
        checkpoint = (ROOT / "docs/ai-cto/checkpoint.md").read_text(encoding="utf-8").split("---", 1)[-1].strip()
        print("AUTO-WAKE AFTER COMPACTION. The conversation was just compacted. Do not wait for the founder "
              "and do not re-derive state: resume the work below now, in order. If the founder lease in the "
              "checkpoint has expired, finish the current item, update the checkpoint, and report.\n")
        print(checkpoint[:3000])
        print("\n== Matrix status\n" + run("observe.status"))
        print("\n== Open founder decisions\n" + run("decide.open"))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
