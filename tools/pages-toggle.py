#!/usr/bin/env python3
"""Inject the Yggdrasil / Well-of-Mimir tier toggle into an assembled Pages tree.

WHY THIS EXISTS
---------------
GitHub serves exactly one Pages site per repo, but the portfolio publishes two tiers of
the same documents:

    _site/                 the Well of Mimir  — built from `main`, vetted knowledge
    _site/yggdrasil/       Yggdrasil          — built from `Yggdrasil`, work in flight

Two trees, one site. Without a visible marker a reader cannot tell which tier a page
belongs to, and a working draft read as vetted doctrine is exactly the provenance
laundering `docs/provenance.html` exists to prevent: transmission never promotes, so a
page must *say* which water it was drawn from.

This walks an assembled tree and inserts a banner at the top of every page naming the
tier and linking to the same document in the other tree. The link is computed per file
from its depth, so it is correct for nested pages (`client/…`, `operator/…`) as well as
the root ones. When a document exists in one tier but not the other the counterpart link
is dropped rather than emitted broken — a dead link would misreport the other tier as
empty.

The banner is inserted as the first child of <body> rather than positioned fixed: it
pushes content down instead of overlaying it, so it cannot occlude an existing layout.

USAGE
-----
    python3 tools/pages-toggle.py --root _site --tier mimir
    python3 tools/pages-toggle.py --root _site/yggdrasil --tier yggdrasil --site-root _site

EXIT CODES
----------
    0  banner injected into every page found (or no pages found — reported, not failed)
    2  the tree to stamp does not exist
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

# The subdirectory the working tier occupies inside the published site.
WORKING_PREFIX = "yggdrasil"

TIERS = {
    "mimir": {
        "label": "Well of Mimir",
        "gloss": "vetted · built from main",
        "other": "Yggdrasil",
        "other_gloss": "see the working draft",
        "accent": "#1f6f5c",
    },
    "yggdrasil": {
        "label": "Yggdrasil",
        "gloss": "working · not yet drawn into the Well",
        "other": "Well of Mimir",
        "other_gloss": "see the vetted version",
        "accent": "#8a5a1b",
    },
}

MARKER = "a777ance-tier-banner"

# Matches the opening <body> tag, with or without attributes.
BODY_RE = re.compile(r"<body\b[^>]*>", re.I)

STYLE = """<style>
.%(marker)s{font-family:'Gill Sans MT','Gill Sans',Calibri,'Trebuchet MS',sans-serif;
display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:baseline;justify-content:space-between;
padding:.55rem 1rem;border-bottom:1px solid rgba(128,128,128,.35);
background:%(accent)s;color:#fff;font-size:.95rem;line-height:1.4}
.%(marker)s a{color:#fff;text-decoration:underline;text-underline-offset:2px}
.%(marker)s .tier{font-weight:700;letter-spacing:.02em}
.%(marker)s .gloss{opacity:.85;font-size:.87em}
</style>"""


def banner(tier: str, counterpart: str | None) -> str:
    t = TIERS[tier]
    style = STYLE % {"marker": MARKER, "accent": t["accent"]}
    if counterpart:
        link = (
            f'<a href="{html.escape(counterpart)}">{html.escape(t["other"])} '
            f'&rarr;</a> <span class="gloss">{html.escape(t["other_gloss"])}</span>'
        )
    else:
        link = f'<span class="gloss">not present in {html.escape(t["other"])}</span>'
    return (
        f'{style}<div class="{MARKER}">'
        f'<span><span class="tier">{html.escape(t["label"])}</span> '
        f'<span class="gloss">{html.escape(t["gloss"])}</span></span>'
        f"<span>{link}</span></div>"
    )


def counterpart_for(rel: pathlib.PurePosixPath, tier: str,
                    site_root: pathlib.Path) -> str | None:
    """Relative URL to the same document in the other tier, or None if absent."""
    depth = len(rel.parts) - 1
    if tier == "mimir":
        target = site_root / WORKING_PREFIX / rel
        up = "./" if depth == 0 else "../" * depth
        return f"{up}{WORKING_PREFIX}/{rel}" if target.exists() else None
    target = site_root / rel
    # From inside yggdrasil/ the site root is one extra level up.
    up = "../" * (depth + 1)
    return f"{up}{rel}" if target.exists() else None


def stamp(path: pathlib.Path, rel: pathlib.PurePosixPath, tier: str,
          site_root: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:  # idempotent — a re-run must not stack banners
        return False
    m = BODY_RE.search(text)
    if not m:
        return False
    block = banner(tier, counterpart_for(rel, tier, site_root))
    path.write_text(text[:m.end()] + block + text[m.end():], encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=pathlib.Path, required=True,
                    help="tree to stamp (e.g. _site or _site/yggdrasil)")
    ap.add_argument("--tier", choices=sorted(TIERS), required=True)
    ap.add_argument("--site-root", type=pathlib.Path,
                    help="published site root (default: --root)")
    args = ap.parse_args()

    root = args.root
    site_root = args.site_root or root
    if not root.is_dir():
        print(f"FATAL no such tree: {root}", file=sys.stderr)
        return 2

    # The working tier lives inside the site root; never stamp it twice.
    skip = (site_root / WORKING_PREFIX).resolve() if args.tier == "mimir" else None

    done = skipped = 0
    for path in sorted(root.rglob("*.html")):
        if skip and skip in path.resolve().parents:
            continue
        rel = pathlib.PurePosixPath(path.relative_to(root).as_posix())
        if stamp(path, rel, args.tier, site_root):
            done += 1
        else:
            skipped += 1

    print(f"{args.tier}: stamped {done} page(s)" + (f", skipped {skipped}" if skipped else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
