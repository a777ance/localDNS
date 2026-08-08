#!/usr/bin/env python3
"""Render the canonical Bifrost briefing block into every A777ance repo's CLAUDE.md.

WHY THIS EXISTS (docs/architecture/warrant-sites.md)
----------------------------------------------------
Bifrost is declared active in every repo, so every repo's CLAUDE.md carries a copy of
the schema. That made the schema a dozen hand-maintained files that are required to
agree — and git cannot help, because git only conflicts when two sessions touch the
*same* file. These are *different* files with an agreement obligation, so two parallel
sessions can each run green checks, each push cleanly, and still leave the portfolio
self-contradictory. That is not hypothetical: when `'` (Ignition) landed in localDNS,
nine sibling briefings silently kept describing a schema without it, and every one of
them individually looked fine.

The rule "Bifrost is active in every repo" was already written down. Writing it down did
nothing — it had an author and no site. So the copies stop being copies: this script
generates them, and `--check` refuses a commit that would ship drift.

USAGE
-----
    python3 tools/sync-briefings.py            # report drift (same as --check)
    python3 tools/sync-briefings.py --write    # render the canonical block everywhere
    python3 tools/sync-briefings.py --root DIR # portfolio root (default: parent of repo)

EXIT CODES
----------
    0  every discovered briefing matches canonical
    1  drift found (or a repo carries no Bifrost block at all)
    2  the canonical source itself is missing/malformed

Repos that are not checked out are skipped, not failed — a session may hold only some of
the portfolio. The skip list is printed so a green run never silently means "checked
nothing."
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "04-user-services/ai-orchestration/briefing-block.md"

START = "<!-- bifrost-briefing:start -->"
END = "<!-- bifrost-briefing:end -->"
GENERATED_NOTE = (
    "<!-- bifrost-briefing:start — GENERATED from "
    "localDNS/04-user-services/ai-orchestration/briefing-block.md "
    "by tools/sync-briefings.py. Do not hand-edit; edit the canonical file and re-run. -->"
)

# The heading the block lives under in a sibling briefing.
SECTION_HEADING = "## Bifrost — active command schema (loads every session)"

# Legacy (unmarked) block bounds, so the first --write can adopt existing copies.
LEGACY_START = "**Bifrost** is the A777ance command-composition schema"
LEGACY_END = "· rendered page: <https://a777ance.github.io/localDNS/bifrost.html>"

# localDNS carries the *long* form in CLAUDE.md §H rather than this condensed block.
# It is not a render target, but its backbone line must still agree — see check_backbone().
SELF = "localDNS"

BACKBONE_RE = re.compile(r"- \*\*Backbone:\*\*(.*?)(?=\n- \*\*|\n\n)", re.S)
# One "`glyph` role-word" pair, e.g. "`@` source" — role is the first word after the glyph.
PAIR_RE = re.compile(r"`{1,2}([^`]+)`{1,2}\s+([a-z][a-z-]*)")


def read_canonical() -> str:
    if not CANONICAL.exists():
        sys.exit(f"FATAL canonical block missing: {CANONICAL}")
    text = CANONICAL.read_text(encoding="utf-8")
    i, j = text.find(START), text.find(END)
    if i < 0 or j < 0 or j < i:
        sys.exit(f"FATAL canonical block has no {START} / {END} pair: {CANONICAL}")
    return text[i + len(START):j].strip("\n")


def discover(root: pathlib.Path) -> list[pathlib.Path]:
    """Every sibling git repo carrying a CLAUDE.md, localDNS excluded."""
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name == SELF or not (d / ".git").exists():
            continue
        if (d / "CLAUDE.md").exists():
            out.append(d / "CLAUDE.md")
    return out


def extract(text: str) -> tuple[str | None, int, int, bool]:
    """Return (current_block, span_start, span_end, is_marked).

    `is_marked` distinguishes a generated block from a legacy hand-written one whose
    content happens to match. A legacy copy is still drift: it is not addressed by the
    generator, so the next canonical edit would leave it behind exactly the way Ignition
    did. Matching content today is not the same as being wired to the source.
    """
    i = text.find("<!-- bifrost-briefing:start")
    if i >= 0:
        head_end = text.find("-->", i)
        j = text.find(END, i)
        if head_end >= 0 and j >= 0:
            return text[head_end + 3:j].strip("\n"), i, j + len(END), True
    i = text.find(LEGACY_START)
    if i >= 0:
        j = text.find(LEGACY_END, i)
        if j >= 0:
            return text[i:j + len(LEGACY_END)], i, j + len(LEGACY_END), False
    return None, -1, -1, False


def render(text: str, block: str) -> str:
    """Splice the canonical block in, adopting a legacy copy or creating the section."""
    marked = f"{GENERATED_NOTE}\n\n{block}\n\n{END}"
    _, s, e, _ = extract(text)
    if s >= 0:
        return text[:s] + marked + text[e:]
    if SECTION_HEADING in text:  # heading present, body missing
        return text.replace(SECTION_HEADING, f"{SECTION_HEADING}\n\n{marked}", 1)
    sep = "" if text.endswith("\n") else "\n"
    return f"{text}{sep}\n---\n\n{SECTION_HEADING}\n\n{marked}\n"


def pairs(line: str) -> dict[str, str]:
    return {g.strip(): role for g, role in PAIR_RE.findall(line)}


def check_backbone(block: str) -> list[str]:
    """The condensed block and localDNS §H are separate artifacts by design; the one thing
    that must never diverge is which glyph means what."""
    self_md = REPO_ROOT / "CLAUDE.md"
    if not self_md.exists():
        return []
    a = BACKBONE_RE.search(block)
    b = BACKBONE_RE.search(self_md.read_text(encoding="utf-8"))
    if not a or not b:
        return ["could not locate a Backbone line in the block and/or localDNS CLAUDE.md §H"]
    pa, pb = pairs(a.group(1)), pairs(b.group(1))
    return [
        f"glyph {g!r}: briefing-block says {pa[g]!r}, localDNS CLAUDE.md §H says {pb[g]!r}"
        for g in sorted(pa.keys() & pb.keys()) if pa[g] != pb[g]
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="render the block (default: check only)")
    ap.add_argument("--root", type=pathlib.Path, default=REPO_ROOT.parent,
                    help="portfolio root holding the sibling repos")
    args = ap.parse_args()

    block = read_canonical()
    targets = discover(args.root)
    if not targets:
        print(f"note  no sibling repos found under {args.root} — nothing to check")

    drift, wrote, ok = [], [], []
    for path in targets:
        text = path.read_text(encoding="utf-8")
        current, _, _, is_marked = extract(text)
        if current == block and is_marked:
            ok.append(path.parent.name)
            continue
        if args.write:
            path.write_text(render(text, block), encoding="utf-8")
            wrote.append(path.parent.name)
        else:
            if current is None:
                why = "no Bifrost block found"
            elif current != block:
                why = "block differs from canonical"
            else:
                why = "block is unmarked — not wired to the generator (one-time migration)"
            drift.append(f"{path.parent.name}/CLAUDE.md: {why}")

    problems = check_backbone(block)

    for name in wrote:
        print(f"sync {name}")
    for name in ok:
        print(f"ok   {name}")
    if problems:
        print("\nFAIL backbone glyph roles disagree between the two briefing tiers")
        for p in problems:
            print(f"     {p}")
    if drift:
        print("\nFAIL Bifrost briefing block drifted from canonical")
        for d in drift:
            print(f"     {d}")
        print("\n     Fix: python3 tools/sync-briefings.py --write")
    if not drift and not problems:
        verb = "synced" if wrote else "match"
        print(f"\nAll {len(ok) + len(wrote)} briefings {verb} canonical; backbone roles agree.")
    return 1 if (drift or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
