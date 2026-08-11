#!/usr/bin/env python3
"""Resolve a conflict in a file whose blocks are GENERATED — by regenerating, not merging.

WHY THIS EXISTS (docs/architecture/norns.md §4b, race 5)
--------------------------------------------------------
Race 5 was the one collision listed as unsolved. Two Norns each run
`tools/sync-briefings.py --write`, each commits the rendered result, and `CLAUDE.md`
conflicts in every sibling repo — nine conflicts in one round, observed 2026-08-08.

Merging the text is the wrong operation. Those blocks are **build output**: the correct
result is not a blend of two renderings, it is whatever the canonical source renders right
now. So this takes one side wholesale and re-runs the generator.

THE SAFETY CONDITION, which is the whole point
-----------------------------------------------
Taking one side wholesale would silently discard the other side's hand-written prose — and
`CLAUDE.md` is generated blocks *inside* hand-written prose. So before touching anything,
it strips the generated regions from all three versions (base, ours, theirs) and compares
what is left:

  * only OUR side changed prose      -> keep ours, regenerate  (theirs was blocks-only)
  * only THEIR side changed prose    -> keep theirs, regenerate (ours was blocks-only)
  * NEITHER changed prose            -> either side, regenerate (pure block conflict)
  * BOTH changed prose               -> REFUSE. A human merges the prose.

That last branch is why this is safe to automate: it does not guess. It automates exactly
the case where the answer is provably determined, and stops where it is not.

A git merge driver could do this invisibly at merge time. Deliberately not done: a merge
driver that is subtly wrong loses content with no one watching, and this runs rarely
enough that an explicit, inspectable step is the better trade.

USAGE
-----
    python3 tools/resolve-generated.py                 # every conflicted file
    python3 tools/resolve-generated.py CLAUDE.md ...   # named files
    python3 tools/resolve-generated.py --check         # say what it would do, change nothing

EXIT CODES
----------
    0  every conflicted file resolved (or nothing to do)
    1  at least one file needs a human (prose changed on both sides), or a stage failed
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

# The conflict happens where the RENDERED copy lives — usually a sibling repo, since
# race 5 is nine sibling CLAUDE.md files conflicting at once. So the repo under repair is
# whichever one contains the working directory, while the generator always runs from
# localDNS, which owns the canonical blocks.
LOCALDNS = pathlib.Path(__file__).resolve().parent.parent
GENERATOR = ("python3", "tools/sync-briefings.py", "--write")


def _repo_of_cwd() -> pathlib.Path:
    r = subprocess.run(("git", "rev-parse", "--show-toplevel"),
                       capture_output=True, text=True)
    return pathlib.Path(r.stdout.strip()) if r.returncode == 0 else LOCALDNS


REPO = _repo_of_cwd()

# A generated region: <!-- name:start ... --> ... <!-- name:end -->
BLOCK_RE = re.compile(r"<!--\s*([a-z0-9-]+):start.*?<!--\s*\1:end\s*-->", re.S)


def git(*a: str, cwd: pathlib.Path | None = None) -> tuple[int, str]:
    r = subprocess.run(("git", "-C", str(cwd or REPO)) + a, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def conflicted() -> list[str]:
    code, out = git("diff", "--name-only", "--diff-filter=U")
    return [l.strip() for l in out.splitlines() if l.strip()] if code == 0 else []


def stage_version(path: str, stage: int) -> str | None:
    """Stage 1 = merge base, 2 = ours, 3 = theirs."""
    code, out = git("show", f":{stage}:{path}")
    return out if code == 0 else None


def prose(text: str | None) -> str | None:
    """The file with every generated region removed — the part a human wrote."""
    if text is None:
        return None
    return re.sub(r"\n{3,}", "\n\n", BLOCK_RE.sub("", text)).strip()


def decide(path: str) -> tuple[str, str]:
    """(action, why). action in: ours, theirs, either, human, no-blocks."""
    base, ours, theirs = (stage_version(path, s) for s in (1, 2, 3))
    if ours is None or theirs is None:
        return "human", "one side is missing (add/delete conflict) — not a block conflict"
    if not BLOCK_RE.search(ours) and not BLOCK_RE.search(theirs):
        return "no-blocks", "no generated regions in this file"

    pb, po, pt = prose(base), prose(ours), prose(theirs)
    ours_touched = po != pb
    theirs_touched = pt != pb

    if ours_touched and theirs_touched:
        if po == pt:
            return "either", "both changed prose IDENTICALLY — the conflict is blocks-only"
        return "human", "prose changed on BOTH sides — a human must merge it"
    if ours_touched:
        return "ours", "only our side changed prose; theirs was blocks-only"
    if theirs_touched:
        return "theirs", "only their side changed prose; ours was blocks-only"
    return "either", "neither side changed prose — a pure generated-block conflict"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--check", action="store_true", help="report only; change nothing")
    args = ap.parse_args()

    files = args.files or conflicted()
    if not files:
        print("no conflicted files — nothing to resolve")
        return 0

    resolved, needs_human = [], []
    for path in files:
        action, why = decide(path)
        print(f"{path}\n  {action.upper():7} {why}")
        if action in ("human", "no-blocks"):
            needs_human.append(path)
            continue
        if args.check:
            resolved.append(path)
            continue

        side = "2" if action == "ours" else "3"        # 'either' -> take theirs
        code, out = git("checkout", f"--{'ours' if side == '2' else 'theirs'}", "--", path)
        if code != 0:
            print(f"  could not take that side: {out.strip()[:160]}")
            needs_human.append(path)
            continue
        resolved.append(path)

    if args.check:
        print(f"\nwould resolve {len(resolved)}, needs a human: {len(needs_human)}")
        return 1 if needs_human else 0

    if resolved:
        gen = subprocess.run(GENERATOR, cwd=LOCALDNS, capture_output=True, text=True)
        if gen.returncode != 0:
            print(f"\ngenerator FAILED — not staging anything:\n{gen.stdout[-400:]}")
            return 1
        print("\nregenerated from canonical")
        for path in resolved:
            leftover = (REPO / path).read_text(encoding="utf-8", errors="replace")
            if "<<<<<<<" in leftover:
                print(f"  {path}: conflict markers SURVIVED — not staging it")
                needs_human.append(path)
                continue
            git("add", "--", path)
            print(f"  staged {path}")

    if needs_human:
        print("\nNEEDS A HUMAN:")
        for p in needs_human:
            print(f"  {p}")
        print("Merge the prose by hand, then re-run the generator before committing.")
        return 1

    print("\nAll conflicts resolved by regeneration. Verify, then continue the rebase/merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
