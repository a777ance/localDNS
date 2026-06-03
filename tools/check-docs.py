#!/usr/bin/env python3
"""Validate Markdown cross-links across the repo's docs.

For every `*.md` file in the repo root:
  - every in-page anchor link `](#slug)` resolves to a heading in the same file
  - every relative file link `](path)` points to a file that exists

Heading anchors are computed with GitHub's slug algorithm (lowercase, drop
characters that are not word/space/hyphen, spaces -> hyphens, de-duplicate with
-1/-2). Headings inside fenced code blocks are ignored, as are links inside
fenced code. External (`http(s)://`, `mailto:`) links are skipped.

Exits non-zero if any link is broken, so it can gate a commit or CI run.

Usage:
    python3 tools/check-docs.py
"""
import glob
import os
import re
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def slugify(text, seen):
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s", "-", s)
    if s in seen:
        seen[s] += 1
        s = f"{s}-{seen[s]}"
    else:
        seen[s] = 0
    return s


def heading_anchors(lines):
    seen, anchors, in_fence = {}, set(), False
    for ln in lines:
        if re.match(r"^\s*```", ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", ln)
        if m:
            anchors.add(slugify(m.group(2), seen))
    return anchors


def strip_fenced(lines):
    out, in_fence = [], False
    for ln in lines:
        if re.match(r"^\s*```", ln):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else ln)
    return out


def check(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    anchors = heading_anchors(lines)
    base = os.path.dirname(path)
    problems = []
    for raw in LINK.findall("\n".join(strip_fenced(lines))):
        target = raw.strip().split(None, 1)[0]  # drop any optional "title"
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            if target[1:] not in anchors:
                problems.append(f"broken anchor link: {raw.strip()}")
            continue
        filepart = target.split("#", 1)[0]
        if filepart and not os.path.exists(os.path.join(base, filepart)):
            problems.append(f"missing file link: {raw.strip()}")
    return problems


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    failed = False
    for f in sorted(glob.glob("*.md")):
        problems = check(f)
        if problems:
            failed = True
            print(f"FAIL {f}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {f}")
    if failed:
        print("\nDoc check FAILED")
        sys.exit(1)
    print("\nAll doc links resolve.")


if __name__ == "__main__":
    main()
