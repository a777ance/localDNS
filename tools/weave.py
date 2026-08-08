#!/usr/bin/env python3
"""Show the current weave: who moved the eye, what is claimed, what is unclaimed.

WHY THIS EXISTS (docs/architecture/norns.md §5)
-----------------------------------------------
Concurrent sessions weave `Yggdrasil` at once and **cannot see each other** — `ListAgents`
returns nothing and the CCR server exposes `create_session` with no `send_message`. Git
catches collisions; nothing catches two Norns being handed the same thread. On 2026-08-08 a
session was spawned to "archive the doom drawer" minutes after the drawer had been built,
verified and pushed, because the spawning session had no way to look.

The repo is the only channel, so looking has to be one command. This is that command. Run
it at session start, and **before spawning another Norn**.

It deliberately does NOT try to match queue items to claims automatically. A fuzzy matcher
that silently mis-matched would be worse than no matcher: it would report "unclaimed" for
work already in flight, which is the exact failure this file exists to prevent. It prints
both columns and leaves the judgement where it belongs.

USAGE
-----
    python3 tools/weave.py            # the weave, as the remote currently has it
    python3 tools/weave.py --local    # skip the fetch (offline / fast)

EXIT CODES
----------
    0  always — this is a viewer, not a gate. It must never block a session from starting.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
NORNS = REPO / "docs/architecture/norns.md"
QUEUE = REPO / "docs/ai-cto/context.md"
BRANCH = "Yggdrasil"


def git(*args: str) -> str:
    try:
        r = subprocess.run(("git", "-C", str(REPO)) + args,
                           capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def rule(title: str) -> None:
    print(f"\n\033[1m── {title} ──\033[0m" if sys.stdout.isatty() else f"\n── {title} ──")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--local", action="store_true", help="skip the network fetch")
    ap.add_argument("-n", type=int, default=8, help="how many recent commits to show")
    args = ap.parse_args()

    if not args.local:
        git("fetch", "origin", BRANCH, "--quiet")

    ref = f"origin/{BRANCH}"
    tip = git("rev-parse", "--short", ref)

    rule("the eye")
    if not tip:
        print(f"  {ref} unreachable — showing local {BRANCH}")
        ref = BRANCH
        tip = git("rev-parse", "--short", ref) or "?"
    local = git("rev-parse", "--short", BRANCH)
    print(f"  {ref} @ {tip}" + (f"   (local {BRANCH} @ {local})" if local and local != tip else ""))

    counts = git("rev-list", "--left-right", "--count", f"{ref}...{BRANCH}")
    if counts and counts.split() == ["0", "0"]:
        print("  you hold it — local and remote agree")
    elif counts:
        behind, ahead = (counts.split() + ["?", "?"])[:2]
        if behind != "0":
            print(f"  ANOTHER NORN HAS MOVED IT — you are {behind} behind. "
                  f"fetch and rebase before you write.")
        if ahead != "0":
            print(f"  you have {ahead} unpushed commit(s) — hand the eye back when done.")

    rule(f"recent weave ({ref})")
    log = git("log", f"-{args.n}", "--format=%ad  %h  %s", "--date=format:%m-%d %H:%M", ref)
    print("\n".join(f"  {l}" for l in log.splitlines()) if log else "  (no history)")

    rule("claims — docs/architecture/norns.md")
    if NORNS.exists():
        rows = [l for l in NORNS.read_text(encoding="utf-8").splitlines()
                if l.startswith("| 2026-") or l.startswith("| 202")]
        print("\n".join(f"  {r}" for r in rows) if rows else "  (no claims recorded)")
    else:
        print("  norns.md missing")

    rule("queue — docs/ai-cto/context.md (Default next actions)")
    if QUEUE.exists():
        text = QUEUE.read_text(encoding="utf-8")
        m = re.search(r"## Default next actions(.*?)\n---", text, re.S)
        if m:
            items = [l.rstrip() for l in m.group(1).splitlines()
                     if re.match(r"^\s*\d+\.\s", l) or l.strip().startswith("**")]
            print("\n".join(f"  {i}" for i in items) if items else "  (queue empty)")
        else:
            print("  (no 'Default next actions' block found)")
    else:
        print("  context.md missing")

    print("\n  Claims are not matched to the queue automatically — read both.")
    print("  Before spawning a Norn: give it an EMPTY lane, not a task that sounds unfinished.")
    print("  Then write the claim (norns.md §4) BEFORE the work, not after.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
