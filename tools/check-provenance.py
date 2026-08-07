#!/usr/bin/env python3
"""Validate provenance tags across the repo — the enforcement half of the
Provenance Ladder (docs/provenance.html).

The doctrine's own root-cause lesson is that prose is advisory: runs inherit
their behaviour from the file that executes them, so an invariant living only in
a briefing gets re-broken by the next operator following that briefing faithfully.
This script is where the ladder becomes load-bearing.

A provenance tag declares where an artifact's authority came from:

    provenance: R · rebuilt from docs/architecture/network-context.md · 2026-08-07 · verify: DEPLOY-QUEUE Stage 13
                ^   ^                                                   ^            ^
                |   source (what it came FROM, not what it describes)   |            how to promote it
                tier (M/O/D/R/A)                                        date the claim was made

Carried in whatever comment syntax the file speaks:

    <!-- provenance: … -->      Markdown, HTML
    # provenance: …             conf, sh, yml, py

Checks (failures, unless noted):
  1. Tier letter is on the ladder; source and date present; date parses and is
     not in the future.
  2. R- or A-tier artifacts that are *deploy targets* (they appear in the
     CLAUDE.md § C repo→system table) must be listed in docs/DEPLOY-QUEUE.md.
     An unverified reconstruction that is not queued for a diff-vs-box is how a
     description of the box becomes the box.
  3. R- and A-tier tags must carry a `verify:` field — the route back to an
     origin outside the loop. A tier with no promotion path is a dead end that
     ages into assumed truth.
  4. M/O tags older than --stale-days (default 180) are reported as STALE
     (warning; --strict promotes it to a failure). Observations decay: the box
     drifts, and a stale reading is not a current one. Staleness never lowers a
     recorded tier — it means re-observe, not re-label.

Coverage of deploy targets is reported but only enforced under --strict, so the
gate can be adopted incrementally without a repo-wide tagging sweep first.

Usage:
    python3 tools/check-provenance.py [--strict] [--stale-days N]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The ladder, highest first (house style: descending).
TIERS = {
    "M": "Measured — a number this stack actually produced; carries the command that produced it",
    "O": "Observed — read off the source of truth (the live t630), not off a description of it",
    "D": "Derived — follows deterministically from stated M/O inputs; no higher than its weakest input",
    "R": "Reconstructed — rebuilt from a description of the thing rather than the thing itself",
    "A": "Asserted — design intent, plan, or lore; no origin outside the author",
}
NEEDS_VERIFY = {"R", "A"}

TAG = re.compile(
    r"(?:<!--|#|//)\s*provenance:\s*(?P<body>[^\n>]*?)\s*(?:-->|$)",
    re.IGNORECASE | re.MULTILINE,
)
SEP = re.compile(r"\s*·\s*|\s+\|\s+")

SCAN_SUFFIXES = {".md", ".html", ".conf", ".yml", ".yaml", ".sh", ".py", ".nft", ".service", ".timer", ".rules", ".cfg", ".js"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".github"}

# This file documents the tag syntax, so its examples are not real tags.
SELF = Path(__file__).relative_to(REPO)


def walk() -> list[Path]:
    out = []
    for p in sorted(REPO.rglob("*")):
        if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(REPO).parts):
            continue
        out.append(p)
    return out


def deploy_targets() -> set[str]:
    """Repo paths named in the CLAUDE.md § C repo→system table."""
    claude = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    targets = set()
    for line in claude.splitlines():
        if not line.startswith("| `"):
            continue
        cell = line.split("|")[1].strip()
        m = re.fullmatch(r"`([^`]+)`", cell)
        if m and (REPO / m.group(1)).exists():
            targets.add(m.group(1))
    return targets


def parse(body: str) -> tuple[dict, list[str]]:
    """Split a tag body into fields; return (fields, structural errors)."""
    parts = [p.strip() for p in SEP.split(body) if p.strip()]
    errs: list[str] = []
    if len(parts) < 3:
        return {}, [f"expected 'TIER · source · date [· verify: …]', got {body!r}"]

    tier = parts[0].upper()
    if tier not in TIERS:
        errs.append(f"unknown tier {parts[0]!r} — the ladder is {'/'.join(TIERS)}")

    date = None
    try:
        date = dt.date.fromisoformat(parts[2])
    except ValueError:
        errs.append(f"date {parts[2]!r} is not ISO YYYY-MM-DD")
    else:
        if date > dt.date.today():
            errs.append(f"date {date} is in the future")

    extras = {}
    for p in parts[3:]:
        if ":" in p:
            k, _, v = p.partition(":")
            extras[k.strip().lower()] = v.strip()

    return {"tier": tier, "source": parts[1], "date": date, **extras}, errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate provenance tags (docs/provenance.html).")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on stale M/O tags and on untagged deploy targets")
    ap.add_argument("--stale-days", type=int, default=180,
                    help="age at which an M/O observation is reported stale (default 180)")
    args = ap.parse_args()

    targets = deploy_targets()
    failures: list[str] = []
    warnings: list[str] = []
    tagged: dict[str, dict] = {}

    for path in walk():
        rel = str(path.relative_to(REPO))
        if rel == str(SELF):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for m in TAG.finditer(text):
            fields, errs = parse(m.group("body"))
            line_no = text[: m.start()].count("\n") + 1
            where = f"{rel}:{line_no}"
            for e in errs:
                failures.append(f"{where}: {e}")
            if not fields:
                continue
            tagged[rel] = fields
            tier = fields["tier"]

            if tier in NEEDS_VERIFY and not fields.get("verify"):
                failures.append(
                    f"{where}: tier {tier} needs a 'verify: …' field — how does this reach "
                    f"an origin outside the loop?"
                )

            if tier in NEEDS_VERIFY and rel in targets:
                queue = (REPO / "docs/DEPLOY-QUEUE.md").read_text(encoding="utf-8")
                if rel not in queue:
                    failures.append(
                        f"{where}: tier {tier} deploy target is not staged in docs/DEPLOY-QUEUE.md — "
                        f"an unverified reconstruction must never reach the box undiffed"
                    )

            if tier in {"M", "O"} and fields.get("date"):
                age = (dt.date.today() - fields["date"]).days
                if age > args.stale_days:
                    msg = (f"{where}: tier {tier} observation is {age} days old "
                           f"(> {args.stale_days}) — re-observe, don't re-label")
                    (failures if args.strict else warnings).append(msg)

    untagged = sorted(t for t in targets if t not in tagged)
    if untagged and args.strict:
        for t in untagged:
            failures.append(f"{t}: deploy target carries no provenance tag")

    for rel in sorted(tagged):
        f = tagged[rel]
        print(f"{f['tier']}    {rel}  ←  {f['source']}  ({f['date']})")

    if warnings:
        print("\nStale (re-observe):")
        for w in warnings:
            print(f"  ! {w}")

    covered = len(targets) - len(untagged)
    print(f"\nDeploy-target coverage: {covered}/{len(targets)} tagged"
          f"{'' if args.strict else '  (run --strict to require full coverage)'}")

    if failures:
        print(f"\n{len(failures)} provenance failure(s):", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1

    print(f"\nAll {len(tagged)} provenance tag(s) valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
