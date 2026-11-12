#!/usr/bin/env python3
"""check-bridge.py — gate for the bridge display (tools/bridge.py).

Draws every panel at four widths, framed and unframed, in colour and plain, and fails if any
panel raises, overflows the screen, or leaks colour codes into plain mode. A display that
crashes on the founder's terminal is worse than no display.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, str(ROOT / "tools/bridge.py"), "--check"], cwd=ROOT).returncode)
