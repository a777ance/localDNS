#!/usr/bin/env python3
"""Build the A777ance design-system bundle.

Composes each authored fragment in `parts/` into a **self-contained** preview in
`previews/` — tokens and base CSS inlined, no external requests — because that is
what a Claude Design card has to be able to render on its own.

Why a build step at all: one source of truth. The palette lives in
`tokens/tokens.css` exactly once. Previews get a copy at build time; nobody
hand-maintains a second one. Same reason `tokens/tokens.json` is generated from
the CSS rather than written beside it — a JSON mirror that drifts is worse than
no JSON at all.

Usage:
    python3 build.py            # build previews/ + tokens.json
    python3 build.py --check    # verify the committed output is up to date (CI)

Standard library only, like every other tool in this repo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = ROOT / "parts"
PREVIEWS = ROOT / "previews"
TOKENS_CSS = ROOT / "tokens" / "tokens.css"
BASE_CSS = ROOT / "tokens" / "base.css"
TOKENS_JSON = ROOT / "tokens" / "tokens.json"

# The Design System pane reads this marker from the first line of each preview.
CARD_RE = re.compile(r"^<!--\s*@dsCard\s+(?P<attrs>.*?)\s*-->\s*$")
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
STYLE_RE = re.compile(r"<style>(.*?)</style>", re.DOTALL)
# Token declarations, plus the trailing `/* … */` comment when there is one.
DECL_RE = re.compile(r"^\s*(--[\w-]+)\s*:\s*(.+?);\s*(?:/\*\s*(.*?)\s*\*/)?\s*$")
# `/* ── Group ── … */` banners divide tokens.css into roles.
GROUP_RE = re.compile(r"/\*\s*[─\-]+\s*(.+?)\s*[─\-]+")

PAGE = """{card}
<meta charset="utf-8">
<title>{title} — A777ance design system</title>
<style>
{css}
</style>
{markup}
"""


class BuildError(Exception):
    """A part is malformed. Fail loudly — a silently skipped component is a
    component that quietly disappears from the design system."""


def parse_part(path: Path) -> dict:
    """Split an authored part into its card metadata, CSS, and markup."""
    raw = path.read_text(encoding="utf-8")
    first, _, rest = raw.partition("\n")

    card = CARD_RE.match(first.strip())
    if not card:
        raise BuildError(f"{path.relative_to(ROOT)}: first line must be an @dsCard comment")

    attrs = dict(ATTR_RE.findall(card.group("attrs")))
    for required in ("group", "name"):
        if not attrs.get(required):
            raise BuildError(f"{path.relative_to(ROOT)}: @dsCard is missing {required}=\"…\"")

    css = "\n".join(m.strip() for m in STYLE_RE.findall(rest))
    markup = STYLE_RE.sub("", rest).strip()
    if not markup:
        raise BuildError(f"{path.relative_to(ROOT)}: no markup after the <style> block")

    return {"path": path, "card": first.strip(), "attrs": attrs, "css": css, "markup": markup}


def compose(part: dict, tokens: str, base: str) -> str:
    """Inline tokens + base + component CSS into one standalone page."""
    css = "\n".join(chunk for chunk in (tokens, base, part["css"]) if chunk.strip())
    return PAGE.format(card=part["card"], title=part["attrs"]["name"], css=css, markup=part["markup"])


def extract_tokens(css: str) -> dict:
    """Read tokens.css into the JSON mirror, keeping each token's role group and
    its inline comment — the comment is usually the only place the *rule* for
    using a token is written down."""
    groups: dict[str, dict] = {}
    current = "Ungrouped"
    in_root = False

    for line in css.splitlines():
        if banner := GROUP_RE.search(line):
            current = banner.group(1).strip()
            continue
        if ":root" in line:
            in_root = True
            continue
        if in_root and line.strip() == "}":
            break
        if not in_root:
            continue
        if decl := DECL_RE.match(line):
            name, value, note = decl.groups()
            entry = {"value": value.strip()}
            if note:
                entry["note"] = note
            groups.setdefault(current, {})[name] = entry

    return groups


def build(check: bool) -> int:
    tokens = TOKENS_CSS.read_text(encoding="utf-8")
    base = BASE_CSS.read_text(encoding="utf-8")

    parts = sorted(PARTS.rglob("*.html"))
    if not parts:
        print("no parts found — nothing to build", file=sys.stderr)
        return 1

    written: list[Path] = []
    stale: list[str] = []

    for path in parts:
        part = parse_part(path)
        out = PREVIEWS / path.relative_to(PARTS)
        page = compose(part, tokens, base)

        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != page:
                stale.append(str(out.relative_to(ROOT)))
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page, encoding="utf-8")
        written.append(out)

    manifest = json.dumps(extract_tokens(tokens), indent=2) + "\n"
    if check:
        if not TOKENS_JSON.exists() or TOKENS_JSON.read_text(encoding="utf-8") != manifest:
            stale.append(str(TOKENS_JSON.relative_to(ROOT)))
    else:
        TOKENS_JSON.write_text(manifest, encoding="utf-8")

    # An orphan is a preview whose part was deleted or renamed. It would still
    # upload and still show a card, so name it rather than leave it lying there.
    orphans = sorted(p for p in PREVIEWS.rglob("*.html") if p not in written)
    for orphan in orphans:
        print(f"orphan preview (no matching part): {orphan.relative_to(ROOT)}", file=sys.stderr)

    if check:
        if stale or orphans:
            for s in stale:
                print(f"stale: {s}", file=sys.stderr)
            print("\nout of date — run: python3 design-system/build.py", file=sys.stderr)
            return 1
        print(f"up to date — {len(written)} previews, {sum(len(g) for g in extract_tokens(tokens).values())} tokens")
        return 0

    print(f"built {len(written)} previews + tokens.json")
    return 1 if orphans else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify committed output matches the sources")
    args = ap.parse_args()
    try:
        return build(args.check)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
