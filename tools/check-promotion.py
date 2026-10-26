#!/usr/bin/env python3
"""Lock the top gate: `main` moves only by a cherry-pick promotion, never a full-branch merge.

WHY THIS EXISTS (docs/architecture/warrant-sites.md)
----------------------------------------------------
The "cream rises" doctrine (CLAUDE.md §3) says promotion into `main` is always a
*strategic, contingent cherry-pick* from Yggdrasil — specific chosen commits on a
`main`-based branch — and **never** a merge of the whole Yggdrasil branch. Stated only in
prose, that rule has an author and no site: a `Yggdrasil -> main` PR is one green button
away, and clicking it merges everything. Silence is an assignment. This check is the
refusal that makes the prohibition real.

THE TWO MECHANICAL RULES (evaluated only for PRs whose base is `main`)
---------------------------------------------------------------------
  1. HEAD-RAIL BAN. The PR head may not be a rail — `Yggdrasil`, `main`, `doombox/*`,
     `doom-drawer/*`, `archive/*`. A promotion rides a `promote/*` branch cut from `main`
     that carries only cherry-picked commits. A PR straight from `Yggdrasil` *is* the
     full-branch merge this forbids.
  2. NO-WHOLE-BRANCH. `origin/Yggdrasil`'s tip must not be an ancestor of the PR head.
     A cherry-pick creates new SHAs, so the Yggdrasil tip never becomes reachable from a
     legitimate promotion; if it IS reachable, the branch was merged in wholesale (rule 1
     evaded by renaming the branch, or Yggdrasil merged into the promote branch).

Either rule tripping is a forbidden promotion. Both passing means: a `promote/*` branch
whose history does not contain the Yggdrasil tip — i.e. a genuine cherry-pick selection.

USAGE
-----
    # CI (base/head come from the pull_request event):
    python3 tools/check-promotion.py --head "$GITHUB_HEAD_REF" --base "$GITHUB_BASE_REF"

    # Local dry-run against a branch you are about to PR:
    python3 tools/check-promotion.py --head promote/cream-rises --base main

The NO-WHOLE-BRANCH test needs the Yggdrasil tip and the head locally; the runner fetches
both first (see .github/workflows/promotion-guard.yml). If the head ref cannot be resolved
locally, only rule 1 is applied and the gap is reported — never silently passed.

EXIT CODES
----------
    0  a legal cherry-pick promotion (or a PR whose base is not `main` — not our concern)
    1  a forbidden full-branch merge, or the head could not be verified where required
"""

from __future__ import annotations

import argparse
import subprocess
import sys

PROTECTED_BASE = "main"
YGGDRASIL = "Yggdrasil"

# A promotion may not come FROM any of these — they are rails, not selections.
RAIL_EXACT = {"Yggdrasil", "main"}
RAIL_PREFIXES = ("doombox/", "doom-drawer/", "archive/")


def _norm(ref: str) -> str:
    """Strip refs/heads/ and origin/ so `--head` accepts a bare branch name or a full ref."""
    for p in ("refs/heads/", "refs/remotes/", "origin/"):
        if ref.startswith(p):
            ref = ref[len(p):]
    return ref


def is_rail(name: str) -> bool:
    return name in RAIL_EXACT or name.startswith(RAIL_PREFIXES)


def _rev_parse(ref: str) -> str | None:
    r = subprocess.run(("git", "rev-parse", "--verify", "--quiet", ref),
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def _is_ancestor(anc: str, desc: str) -> bool:
    return subprocess.run(("git", "merge-base", "--is-ancestor", anc, desc),
                          capture_output=True).returncode == 0


def resolve_head(head: str) -> str | None:
    """Best-effort resolve the head branch to a commit we hold locally."""
    for cand in (f"origin/{head}", head, f"refs/heads/{head}"):
        sha = _rev_parse(cand)
        if sha:
            return sha
    return None


def check(head: str, base: str) -> int:
    base, head = _norm(base), _norm(head)

    if base != PROTECTED_BASE:
        print(f"ok    base is '{base}', not '{PROTECTED_BASE}' — promotion lock does not apply")
        return 0

    print(f"promotion into '{base}': head is '{head}'")

    # Rule 1 — HEAD-RAIL BAN.
    if is_rail(head):
        print(f"\nFAIL forbidden full-branch merge into `main`.")
        print(f"  '{head}' is a rail. `main` moves ONLY by a cherry-pick promotion:")
        print(f"  cut a `promote/*` branch FROM main, cherry-pick the chosen commits onto")
        print(f"  it, and open the PR from THAT branch. Never PR a rail into main.")
        return 1

    if not head.startswith("promote/"):
        # Not fatal by itself, but the sanctioned vehicle is promote/* — say so loudly.
        print(f"warn  head '{head}' is not a `promote/*` branch; the sanctioned promotion "
              f"vehicle is a promote/* branch cut from main.")

    # Rule 2 — NO-WHOLE-BRANCH.
    ygg = _rev_parse(f"origin/{YGGDRASIL}") or _rev_parse(YGGDRASIL)
    head_sha = resolve_head(head)

    if ygg is None:
        print("warn  could not resolve origin/Yggdrasil locally — NO-WHOLE-BRANCH test "
              "skipped (fetch Yggdrasil to enforce it). Rule 1 still applied.")
        print("\nok    head is not a rail; whole-branch test unverified but not violated")
        return 0

    if head_sha is None:
        print(f"\nFAIL could not resolve head '{head}' locally, so the NO-WHOLE-BRANCH test "
              f"cannot run. Fetch the head branch; a promotion is not certified unverified.")
        return 1

    if _is_ancestor(ygg, head_sha):
        print(f"\nFAIL forbidden full-branch merge into `main`.")
        print(f"  origin/Yggdrasil ({ygg[:10]}) is an ancestor of the head — the whole")
        print(f"  branch is present, so this promotes Yggdrasil wholesale, not a selection.")
        print(f"  Cherry-pick the specific commits onto a fresh promote/* branch instead.")
        return 1

    print(f"\nok    cherry-pick promotion — head does not contain the Yggdrasil tip "
          f"({ygg[:10]}); a genuine selection")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--head", required=True, help="PR head branch (source of the promotion)")
    ap.add_argument("--base", required=True, help="PR base branch (destination)")
    args = ap.parse_args()
    return check(args.head, args.base)


if __name__ == "__main__":
    raise SystemExit(main())
