#!/usr/bin/env python3
"""PreCompact hook — says what the compaction summary must keep.

Its stdout is passed to the compaction as instructions: keep the lease times, the open
founder decisions, the current queue item, and the last shipped commit, and point at
docs/ai-cto/checkpoint.md for everything else. Output stays under 1,200 characters.
Never blocks a compaction. Fails open. Standard library only.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, timeout=4).stdout.strip()


def read(rel: str) -> str:
    f = ROOT / rel
    return f.read_text(encoding="utf-8") if f.exists() else ""


def main() -> int:
    try:
        handoff = read("docs/ai-cto/handoff.md")
        queue = read("docs/ai-cto/superqueue.md") or handoff  # the superqueue is the queue, where it exists
        lease = re.search(r"`(start: [^`]*expiry: [^`]*)`", handoff)
        item = next((m for m in re.finditer(r"^- \*\*(S?Q-\d{3}) · (.*?)\*\*.*$", queue, re.MULTILINE)
                     if not re.search("BLOCKED|DONE|SKIPPED", m.group(0))), None)
        opens = re.findall(r"^- \*\*(DEC-\d{3}) · .*? · OPEN\*\*", read("docs/ai-cto/blocked.md"), re.MULTILINE)
        dirty = git("status", "--short")
        out = ("The summary MUST keep these facts word for word:\n"
               f"- Branch: {git('branch', '--show-current') or '(none)'}\n"
               f"- Lease: {lease.group(1) if lease else 'none recorded'}\n"
               f"- Open founder decisions: {', '.join(opens) or 'none'}\n"
               f"- Current queue item: {item.group(1) + ' · ' + item.group(2)[:80] if item else 'none left unblocked'}\n"
               f"- Last shipped commit: {git('log', '--format=%h %s', '-1')[:110]}\n"
               "- All other state is on disk in docs/ai-cto/checkpoint.md and docs/ai-cto/superqueue.md; "
               "the summary should say to read them first and then resume the queue without waiting.\n")
        if dirty:
            out += (f"- UNCOMMITTED WORK in {len(dirty.splitlines())} file(s): {', '.join(l.split()[-1] for l in dirty.splitlines())[:300]}. "
                    "Say so, and that it must be shipped first.\n")
        print(out[:1190])
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
