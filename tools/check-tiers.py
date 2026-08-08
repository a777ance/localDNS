#!/usr/bin/env python3
"""Report the gap between the two tiers, and refuse a commit made on the vetted one.

WHY THIS EXISTS (docs/architecture/warrant-sites.md)
----------------------------------------------------
ADR-008 split the portfolio into a working tier (`Yggdrasil`) and a vetted tier (`main`),
and named its own risk in the same breath: *a long-lived branch that never merges does not
remove merge debt, it concentrates it.* Then it handled that risk by saying "watch the gap."

That is an author with no site — briefing prose, read once, outside the read path of every
run that could let the gap grow. The session that spent a day migrating invariants out of
prose and into checks left this one in prose. Same failure, new costume.

The gap is dangerous in a specific, mechanical way. **A fresh session clones the DEFAULT
branch**, which is `main`. So everything written on `Yggdrasil` — including the rule that
says to write on `Yggdrasil` — is invisible to the next session until someone merges. A
drawer that things go into and nothing reads out of. Left alone it does not decay slowly;
it misinforms the very next clone.

WHAT THIS CHECKS
----------------
1. **Refuses a commit on `main`** (exit 1). This is the mechanical half of "push to
   Yggdrasil, never to main", and it is *session-fixable* — the run switches branch and
   proceeds. That is the bar for a blocking check: it must fail on something the run can
   actually clear.
2. **Reports the drawer depth** — how far the working tier runs ahead of the vetted one,
   and how old the oldest unmerged commit is. Non-blocking, on purpose: the fix for a deep
   drawer is a merge only the founder can approve, and a gate that wedges the repo on a
   condition the run cannot clear gets bypassed, and a bypassed gate is no site at all.
3. **Names the doctrine gap** — whether `main`'s briefing yet carries the branch policy.
   While it does not, every fresh clone reads a briefing that does not mention Yggdrasil.

Network-free: reads only local remote-tracking refs, so it is safe in a commit hook. If the
refs are absent (a shallow or single-branch checkout) it reports that and passes, per the
gate's asymmetric policy — a check whose own plumbing is missing must not block a commit.

USAGE
-----
    python3 tools/check-tiers.py           # report; exit 1 only if committing on main
    python3 tools/check-tiers.py --quiet   # one line unless something is wrong

EXIT CODES
----------
    0  not on the vetted tier (drawer depth reported)
    1  HEAD is the vetted tier — commit refused
"""

from __future__ import annotations

import argparse
import subprocess
import sys

VETTED = "main"
WORKING = "Yggdrasil"


def git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true", help="suppress the all-clear detail")
    args = ap.parse_args()

    head = git("rev-parse", "--abbrev-ref", "HEAD")
    if head is None:
        print("skip  not a git work tree")
        return 0

    # 1. The blocking half — mechanical, and clearable by the run itself.
    if head == VETTED:
        print(
            f"FAIL committing on `{VETTED}` — the vetted tier.\n"
            f"     `{VETTED}` is the Well of Mimir: it moves only through a pull request the\n"
            f"     founder approves, never by a local commit (ADR-008).\n\n"
            f"     Fix: git checkout {WORKING}   (create it from here if it does not exist)\n"
            f"     Then commit again. Nothing is lost — the work is still in your tree."
        )
        return 1

    # 2 & 3. The reporting half — never blocks.
    vetted = git("rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{VETTED}")
    working = git("rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{WORKING}")
    if not vetted or not working:
        missing = VETTED if not vetted else WORKING
        print(f"skip  no local ref for origin/{missing} — cannot measure the tier gap")
        return 0

    depth = git("rev-list", "--count", f"origin/{VETTED}..origin/{WORKING}")
    oldest = git("log", "--format=%ad", "--date=short",
                 f"origin/{VETTED}..origin/{WORKING}")
    oldest_date = oldest.splitlines()[-1] if oldest else None
    n = int(depth) if depth and depth.isdigit() else 0

    if n == 0:
        if not args.quiet:
            print(f"ok   tiers level — origin/{WORKING} has nothing origin/{VETTED} lacks")
        return 0

    # Does the vetted tier yet carry the policy that governs where work goes?
    briefing = git("show", f"origin/{VETTED}:CLAUDE.md")
    policy_landed = bool(briefing) and WORKING in briefing

    print(f"note  drawer depth: origin/{WORKING} is {n} commit(s) ahead of "
          f"origin/{VETTED}" + (f", oldest unmerged {oldest_date}" if oldest_date else ""))
    if not policy_landed:
        print(f"WARN  origin/{VETTED}/CLAUDE.md does not mention `{WORKING}`.")
        print(f"      A fresh session clones the DEFAULT branch, so until this merges every")
        print(f"      new session reads a briefing with no branch rule — and a session")
        print(f"      reading silence invents one. That is what cut 337 stale branches.")
        print(f"      This does not block a commit: only an approved PR can clear it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
