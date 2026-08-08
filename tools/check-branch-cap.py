#!/usr/bin/env python3
"""Enforce the branch cap: no A777ance repo carries more than 9 branches.

WHY THIS EXISTS (docs/architecture/warrant-sites.md)
----------------------------------------------------
"Push to a session branch" produced 338 stale `claude/*` refs across ten repos — 226 of
them holding commits that existed nowhere else. The rule that would have prevented it
("one standing working branch") was written down and had no site, so every session
correctly followed its own harness instruction and minted another branch.

A cap only binds if something refuses. This is that something.

PENDING vs NEW — the distinction that makes the check usable
------------------------------------------------------------
A cap that fails the moment it is written cannot be committed: the gate would block the
very commit adding it. Worse, a check that is switched off (or bypassed forever) is back
to having no site. So the overage is split:

  * PENDING — a `claude/*` branch whose tip is already reachable from a `doom-drawer/*`
    (or legacy `archive/*`) branch in the same repo. Its history is preserved; only the
    ref deletion is outstanding, and deletion is blocked (HTTP 403) from the agent
    environment. Reported loudly, does NOT fail.
  * NEW — anything else over the cap. Fails.

So emptying the desk around the drawer makes the warning disappear on its own, while a
fresh session branch trips the gate the day it appears. The pending state is a stated debt
with a name, not silence — and silence is an assignment.

NETWORK POLICY
--------------
Remote state is the real state, but a commit must not depend on the network. If a repo's
remote cannot be reached, that repo is SKIPPED and named — a green run never silently
means "checked nothing."

USAGE
-----
    python3 tools/check-branch-cap.py             # check every sibling repo
    python3 tools/check-branch-cap.py --cap 9
    python3 tools/check-branch-cap.py --strict    # PENDING also fails

EXIT CODES
----------
    0  every reachable repo within cap (pending overage reported, not failed)
    1  a repo is over cap for reasons other than pending deletions
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

DEFAULT_CAP = 9

# The DOOM DRAWER — "Didn't Organize, Only Moved". The ADHD filing trick, applied to
# refs: one drawer you can stuff things into without sorting them, precisely so nothing
# has to be thrown away to get the desk clear. A branch whose tip is reachable from here
# is *kept*, not tidied — which is the whole reason deleting the ref is safe.
# `archive/` stays recognised: it is the older name for the same idea, and localDNS
# carries a pre-existing `archive/main-pre-consolidation`.
DRAWER_PREFIXES = ("doom-drawer/", "archive/")
SESSION_PREFIX = "claude/"


def git(repo: pathlib.Path, *args: str, timeout: int = 30) -> str | None:
    try:
        r = subprocess.run(("git", "-C", str(repo)) + args,
                           capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


def remote_branches(repo: pathlib.Path) -> dict[str, str] | None:
    out = git(repo, "ls-remote", "--heads", "origin")
    if out is None:
        return None
    branches = {}
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/"):
            branches[ref[len("refs/heads/"):]] = sha.strip()
    return branches


def reachable(repo: pathlib.Path, tip: str, anchors: list[str]) -> bool:
    """True if `tip` is contained in any anchor commit we hold locally."""
    for a in anchors:
        r = subprocess.run(("git", "-C", str(repo), "merge-base", "--is-ancestor", tip, a),
                           capture_output=True)
        if r.returncode == 0:
            return True
    return False


def discover(root: pathlib.Path) -> list[pathlib.Path]:
    return [d for d in sorted(root.iterdir()) if (d / ".git").exists()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--strict", action="store_true",
                    help="pending (archived) overage fails too")
    ap.add_argument("--root", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent.parent.parent)
    args = ap.parse_args()

    failures, pending_repos, skipped, ok = [], [], [], []

    for repo in discover(args.root):
        branches = remote_branches(repo)
        if branches is None:
            skipped.append(repo.name)
            continue
        if len(branches) <= args.cap:
            ok.append(f"{repo.name} ({len(branches)})")
            continue

        anchors = [sha for name, sha in branches.items()
                   if name.startswith(DRAWER_PREFIXES)]
        anchors = [a for a in anchors
                   if subprocess.run(("git", "-C", str(repo), "cat-file", "-e", a + "^{commit}"),
                                     capture_output=True).returncode == 0]

        pending = sum(1 for name, sha in branches.items()
                      if name.startswith(SESSION_PREFIX) and reachable(repo, sha, anchors))
        effective = len(branches) - pending

        if effective > args.cap or (args.strict and pending):
            failures.append(
                f"{repo.name}: {len(branches)} branches, cap {args.cap} "
                f"({pending} in the doom drawer, {effective} effective)")
        else:
            pending_repos.append(
                f"{repo.name}: {len(branches)} branches — {pending} in the doom drawer, awaiting "
                f"deletion; {effective} effective (within cap)")

    for line in ok:
        print(f"ok      {line}")
    for line in pending_repos:
        print(f"PENDING {line}")
    for name in skipped:
        print(f"skip    {name} (remote unreachable — NOT checked)")

    if failures:
        print(f"\nFAIL branch cap exceeded (cap={args.cap})")
        for f in failures:
            print(f"  {f}")
        print("\nRetire stale refs, or archive them first so no history is lost:")
        print("  git log --oneline doom-drawer/* --not origin/Yggdrasil")
        return 1

    if pending_repos:
        print("\nPending deletions are in the doom drawer (Didn't Organize, Only Moved) — "
              "retiring them clears this notice. Nothing is lost; the drawer is kept.")
    print(f"\nBranch cap {args.cap}: OK"
          + (f" ({len(skipped)} repo(s) skipped)" if skipped else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
