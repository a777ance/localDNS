#!/usr/bin/env python3
"""Validate Markdown cross-links AND repo-path references across every doc.

For every `*.md` file in the repo (recursively, excluding `.git`):
  - every in-page anchor link `](#slug)` resolves to a heading in the same file
  - every relative file link `](path)` resolves — tried both relative to the
    doc's own directory and relative to the repo root (these docs mix both
    conventions: `](network-context.md)` is file-relative, `](vault/README.md)`
    is repo-root-relative)
  - every inline-code token that *looks like a repo path* (`` `01-core-network/…` ``,
    `` `vault/seal.sh` ``) points to a file/dir that exists
  - any reference to a legacy 1.x folder path (`01-unbound/…`, `12-secrets/…`, …)
    is a hard FAILURE — those folders were consolidated into the 2.0 layout, so a
    slashed legacy path is stale drift. This is the tripwire that would have caught
    the 195 rotted `docs/` references the 2.0 migration left behind.

Plus one cross-file invariant: the **Bifrost schema card** — the fixed block a bare
`'` returns — must be byte-identical in all three surfaces that carry it. That
answer is specified as a lookup rather than a generation, so the sources have to
agree or the promise is empty. See `check_bifrost_card` below.

Heading anchors use GitHub's slug algorithm. Headings/links inside fenced code
are ignored. External (`http(s)://`, `mailto:`) links are skipped. Absolute
system paths (`/etc/…`) and cross-repo paths (first segment not a repo dir) are
not repo paths and are skipped.

Intentionally-absent paths (e.g. the un-snapshotted Odin subsystem) are listed in
ALLOW_MISSING so they don't trip the check while they remain documented-but-absent.

Exits non-zero if anything is broken, so it can gate a commit or CI run.

Usage:
    python3 tools/check-docs.py
"""
import glob
import html
import os
import re
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INLINE = re.compile(r"`([^`]+)`")

# Real top-level entries a repo-relative path can start with.
REPO_TOP = {
    "01-core-network", "02-performance", "03-monitoring", "04-user-services",
    "vault", "tools", "docs",
}

# Legacy 1.x folder names (pre-consolidation). A slashed reference to any of these
# is stale — the 2.0 migration moved them. Bare mentions (no slash, e.g. the
# "10-llm-router -> 10-ai-orchestration" rename history) are narrative, not paths.
LEGACY = re.compile(
    r"^(?:0[1-9]|1[0-2])-"
    r"(?:unbound|pihole|host-dns|ufw|wireguard|cake|uptime-kuma|"
    r"gpu-performance|remote-desktop|ai-orchestration|console|secrets|llm-router)/"
)

# Documented but intentionally not yet snapshotted (repo-root-relative, no trailing
# slash). Kept explicit so a real new dangling path still fails loudly.
ALLOW_MISSING = {
    "04-user-services/ai-orchestration/langgraph-router",
    "04-user-services/ai-orchestration/langgraph-router/requirements.txt",
    "04-user-services/ai-orchestration/ORCHESTRATION-BLUEPRINT.md",
    # Runtime-created / git-ignored working dirs — referenced in docs, never committed.
    "vault/cleartext",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def path_exists(rel, filedir):
    """True if `rel` resolves relative to the doc's dir OR the repo root.
    Glob tokens (`*`) are satisfied when their parent directory exists."""
    rel = rel.rstrip("/")
    bases = [filedir, ROOT]
    if "*" in rel:
        parent = os.path.dirname(rel)
        return any(os.path.isdir(os.path.join(b, parent)) for b in bases)
    return any(os.path.exists(os.path.join(b, rel)) for b in bases)


def looks_like_repo_path(tok):
    """A token is a repo-path candidate if it is slashed and its first segment is
    a real repo top-level dir (so `/etc/…`, `https://…`, and lore names are out)."""
    if "/" not in tok:
        return False
    first = tok.split("/", 1)[0]
    return first in REPO_TOP


def candidate_tokens(text):
    """Path-ish tokens from inline-code spans (commands may embed a path).

    A Markdown code span never crosses a blank line, so scan paragraph by
    paragraph. Without this, a single unbalanced backtick (e.g. the `` ` ``
    escapes in the Bifrost section) pairs the `INLINE` regex across blank lines
    and swallows a later `[text](path)` link into one span — misreading the
    `path](path` fragment as a bogus repo path. Paragraph scoping confines a
    stray backtick to its own paragraph so it can't reach an unrelated link.
    """
    toks = []
    for para in re.split(r"\n\s*\n", text):
        for span in INLINE.findall(para):
            for t in span.split():
                t = t.strip("`").rstrip(".,;:!?").strip("()[]<>\"'")
                if t:
                    toks.append(t)
    return toks


def check(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    anchors = heading_anchors(lines)
    filedir = os.path.dirname(os.path.abspath(path))
    body = "\n".join(strip_fenced(lines))
    problems = []

    def verdict(tok, kind):
        if LEGACY.match(tok):
            problems.append(f"legacy 1.x path ({kind}): `{tok}`")
            return
        norm = tok.rstrip("/")
        if norm in ALLOW_MISSING:
            return
        if not path_exists(tok, filedir):
            problems.append(f"unresolved path ({kind}): `{tok}`")

    # Markdown links: anchors + file/repo paths.
    for raw in LINK.findall(body):
        target = raw.strip().split(None, 1)[0]
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            if target[1:] not in anchors:
                problems.append(f"broken anchor link: {raw.strip()}")
            continue
        filepart = target.split("#", 1)[0]
        if not filepart:
            continue
        if LEGACY.match(filepart):
            problems.append(f"legacy 1.x path (link): `{filepart}`")
        elif filepart.rstrip("/") not in ALLOW_MISSING and not path_exists(filepart, filedir):
            problems.append(f"missing file link: {raw.strip()}")

    # Inline-code repo-path references.
    for tok in candidate_tokens(body):
        if LEGACY.match(tok) or looks_like_repo_path(tok):
            verdict(tok, "inline")

    return problems


# --- Bifrost schema card: the three copies must be byte-identical -------------
#
# A bare `'` is the Bifrost reference call, and its answer is specified as a
# LOOKUP, not a generation: the same bytes every call. That promise is only worth
# anything if the sources agree, so the card is embedded between
# `bifrost-card:start` / `:end` markers in each surface and compared here.
# CLAUDE.md §H is canonical — it is the copy in context when the call is answered.
CARD_MARK = re.compile(
    r"bifrost-card:start\b.*?-->(.*?)<!--\s*bifrost-card:end", re.S
)
CARD_FILES = [
    "CLAUDE.md",  # canonical — keep first
    "04-user-services/ai-orchestration/highway-notation.md",
    "docs/bifrost.html",
]


def normalize_card(raw, is_html):
    """Reduce an embedded card to its bare text lines.

    Strips the container each surface wraps it in — Markdown fences, blockquote
    `> ` prefixes, HTML tags/entities, and any common leading indent (CLAUDE.md
    nests the card inside a bullet). What survives is the card itself, so a real
    wording drift fails while a re-indent does not.
    """
    if is_html:
        # Take the <pre> body only: source indentation before the opening tag is
        # outside the element (it never renders), so including it would flag a
        # cosmetic re-indent of the HTML as a card drift.
        pre = re.search(r"<pre[^>]*>(.*?)</pre>", raw, re.S)
        raw = pre.group(1) if pre else raw
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = html.unescape(raw)
    lines = []
    for ln in raw.split("\n"):
        ln = re.sub(r"^\s*>\s?", "", ln)          # blockquote prefix
        if re.match(r"^\s*```", ln):              # fence open/close
            continue
        lines.append(ln.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    body = [ln for ln in lines if ln.strip()]
    if body:
        indent = min(len(ln) - len(ln.lstrip()) for ln in body)
        lines = [ln[indent:] if ln.strip() else "" for ln in lines]
    return "\n".join(lines)


def check_bifrost_card():
    cards, problems = {}, []
    for rel in CARD_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            problems.append(f"{rel}: missing (expected to carry the Bifrost card)")
            continue
        m = CARD_MARK.search(open(p, encoding="utf-8").read())
        if not m:
            problems.append(f"{rel}: no bifrost-card:start/end block found")
            continue
        cards[rel] = normalize_card(m.group(1), rel.endswith(".html"))
    if problems:
        return problems
    canon_name = CARD_FILES[0]
    canon = cards[canon_name]
    for rel, text in cards.items():
        if rel == canon_name or text == canon:
            continue
        problems.append(f"{rel}: card differs from {canon_name} (canonical)")
        want, got = canon.split("\n"), text.split("\n")
        for i in range(max(len(want), len(got))):
            w = want[i] if i < len(want) else "<missing>"
            g = got[i] if i < len(got) else "<missing>"
            if w != g:
                problems.append(f"    line {i + 1}: expected {w!r}")
                problems.append(f"              found    {g!r}")
    return problems


def main():
    os.chdir(ROOT)
    md = sorted(
        p for p in glob.glob("**/*.md", recursive=True)
        if not p.startswith(".git" + os.sep)
    )
    failed = False
    for f in md:
        problems = check(f)
        if problems:
            failed = True
            print(f"FAIL {f}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {f}")
    card_problems = check_bifrost_card()
    if card_problems:
        failed = True
        print("FAIL Bifrost schema card (bare `'` reference call)")
        for p in card_problems:
            print(f"  - {p}")
    else:
        print(f"ok   Bifrost schema card identical across {len(CARD_FILES)} surfaces")

    if failed:
        print("\nDoc check FAILED")
        sys.exit(1)
    print(f"\nAll {len(md)} docs: links + repo-path references resolve.")


if __name__ == "__main__":
    main()
