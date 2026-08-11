#!/usr/bin/env python3
"""Ratatoskr — the squirrel who carries commits up the tree. A courier, never a judge.

WHY THIS EXISTS (docs/architecture/yggdrasil-bestiary.md)
--------------------------------------------------------
Ratatoskr runs up and down Yggdrasil carrying messages he did not write. Here he is the
agentic cherry-picker: given commits SOMEONE ELSE chose, he *carries* them one rung up the
ladder (a feature branch -> a doom box -> Yggdrasil). He does not decide what is cream —
that judgment is Odin's (the founder's). A squirrel that chose what to promote, or that
could reach the well, would be the misaligned system this repo keeps locking out.

THE EAGLE BOUNDS HIM — he never carries into `main` (the Well of Mimir).
-----------------------------------------------------------------------
The well is fed only by the founder's approved cherry-pick PR, refused-by-default to
everything else by `tools/check-promotion.py` (the eagle). Ratatoskr enforces the same
edge locally and early: a `--to main` (or any rail that is not a doom box / Yggdrasil) is
refused here, before a courier ever touches it. This is a SITE, not a reminder — the bound
lives in the code that carries, not only in the prose that describes it.

WHAT HE WILL AND WON'T DO
-------------------------
  * WILL carry chosen commits onto a writable rung: `doombox/1-messy`,
    `doombox/2-draft-main`, or `Yggdrasil` — by cherry-pick, preserving authorship.
  * WON'T carry into `main` (the eagle chases him off), and WON'T invent the selection:
    every SHA to carry is passed in, never discovered by the courier.
  * WON'T force-push a rail, and WON'T carry the whole branch (that is the full-branch
    merge the ladder forbids) — he carries the specific commits named, nothing more.

USAGE
-----
    # Dry-run (default): show exactly what would be carried, touch nothing.
    python3 tools/ratatoskr.py --to Yggdrasil <sha> [<sha> ...]
    python3 tools/ratatoskr.py --to doombox/1-messy <sha> --from claude/my-feature

    # Actually carry (still local; push is a separate, deliberate step):
    python3 tools/ratatoskr.py --to Yggdrasil <sha> --carry

EXIT CODES
----------
    0  carry is legal (dry-run reported, or --carry succeeded)
    1  refused (destination is the well or a forbidden rail; bad SHA; cherry-pick conflict)
"""

from __future__ import annotations

import argparse
import subprocess
import sys

# Rungs a courier may deliver onto. `main` is deliberately ABSENT — the eagle.
WRITABLE_RUNGS = ("doombox/1-messy", "doombox/2-draft-main", "Yggdrasil")
THE_WELL = "main"


def git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(("git", *args), capture_output=True, text=True, check=check)


def resolve(sha: str) -> str | None:
    r = git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
    return r.stdout.strip() or None


def one_line(sha: str) -> str:
    return git("show", "-s", "--format=%h %s", sha).stdout.strip()


def refuse(msg: str) -> int:
    print(f"\nRATATOSKR REFUSES.\n  {msg}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("shas", nargs="+", help="the commit(s) to carry — chosen by Odin, not by the squirrel")
    ap.add_argument("--to", required=True, help="destination rung (a doom box or Yggdrasil; never main)")
    ap.add_argument("--from", dest="frm", default=None,
                    help="optional: the branch the commits come from, for the log line only")
    ap.add_argument("--carry", action="store_true",
                    help="actually cherry-pick (default is a dry-run that touches nothing)")
    args = ap.parse_args()

    dest = args.to

    # THE EAGLE. The well is Odin's; a courier never reaches it.
    if dest == THE_WELL:
        return refuse(
            "`main` is the Well of Mimir. Ratatoskr never carries into the well — it is fed "
            "only by the founder's approved cherry-pick PR, and the eagle (promotion-guard) "
            "chases the courier off. Carry to Yggdrasil, then let Odin drink.")
    if dest not in WRITABLE_RUNGS:
        return refuse(
            f"'{dest}' is not a rung a courier may deliver onto. Writable rungs: "
            f"{', '.join(WRITABLE_RUNGS)}. (Rails other than these are not the squirrel's road.)")

    # The selection is given, never discovered. Resolve each chosen commit.
    resolved: list[str] = []
    for s in args.shas:
        full = resolve(s)
        if full is None:
            return refuse(f"cannot resolve commit '{s}' — a courier carries real messages, not rumors.")
        resolved.append(full)

    src = f" from {args.frm}" if args.frm else ""
    print(f"Ratatoskr will carry {len(resolved)} commit(s){src} -> {dest}:")
    for full in resolved:
        print(f"    {one_line(full)}")

    if not args.carry:
        print("\n(dry-run — nothing carried. Re-run with --carry to cherry-pick onto "
              f"{dest}. Push is a separate, deliberate step.)")
        return 0

    # Carry onto the destination rung, on a scratch checkout so we never disturb HEAD's
    # working state. The founder pushes; the squirrel only stacks the commits.
    cur = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if cur != dest:
        co = git("checkout", dest)
        if co.returncode != 0:
            return refuse(f"could not check out '{dest}':\n  {co.stderr.strip()}")

    for full in resolved:
        cp = git("cherry-pick", full)
        if cp.returncode != 0:
            git("cherry-pick", "--abort")
            if cur != dest:
                git("checkout", cur)
            return refuse(
                f"cherry-pick of {one_line(full)} hit a conflict — the squirrel does not "
                f"resolve conflicts (that is a judgment call for a Norn). Aborted cleanly.")
        print(f"  carried {one_line(full)}")

    print(f"\nCarried onto {dest}. Nothing pushed — review, then push deliberately "
          f"(`git push -u origin {dest}`; never force a rail).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
