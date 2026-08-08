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

Plus one cross-file invariant: the **Bifrost sweep string** — the fixed string a bare
`'` returns — must be byte-identical in all three surfaces that carry it. That
answer is specified as a lookup rather than a generation, so the sources have to
agree or the promise is empty. See `check_bifrost_sweep` below.

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


# --- Bifrost sweep string: the three copies must be byte-identical -------------
#
# A bare `'` is the Bifrost reference call, and its answer is specified as a
# LOOKUP, not a generation: the same bytes every call. That promise is only worth
# anything if the sources agree, so the string is embedded between
# `bifrost-sweep:start` / `:end` markers in each surface and compared here.
# CLAUDE.md §H is canonical — it is the copy in context when the call is answered.
SWEEP_MARK = re.compile(
    r"bifrost-sweep:start\b.*?-->(.*?)<!--\s*bifrost-sweep:end", re.S
)
SWEEP_FILES = [
    "CLAUDE.md",  # canonical — keep first
    "04-user-services/ai-orchestration/highway-notation.md",
    "docs/bifrost.html",
]


def normalize_sweep(raw, is_html):
    """Reduce an embedded sweep block to its bare text lines.

    Strips the container each surface wraps it in — Markdown fences, blockquote
    `> ` prefixes, HTML tags/entities, and any common leading indent (CLAUDE.md
    nests it inside a bullet). What survives is the string itself, so a real
    wording drift fails while a re-indent does not.
    """
    if is_html:
        # Take the <pre> body only: source indentation before the opening tag is
        # outside the element (it never renders), so including it would flag a
        # cosmetic re-indent of the HTML as a drift.
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


def check_bifrost_sweep():
    sweeps, problems = {}, []
    for rel in SWEEP_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            problems.append(f"{rel}: missing (expected to carry the Bifrost sweep)")
            continue
        m = SWEEP_MARK.search(open(p, encoding="utf-8").read())
        if not m:
            problems.append(f"{rel}: no bifrost-sweep:start/end block found")
            continue
        sweeps[rel] = normalize_sweep(m.group(1), rel.endswith(".html"))
    if problems:
        return problems
    canon_name = SWEEP_FILES[0]
    canon = sweeps[canon_name]
    for rel, text in sweeps.items():
        if rel == canon_name or text == canon:
            continue
        problems.append(f"{rel}: sweep string differs from {canon_name} (canonical)")
        want, got = canon.split("\n"), text.split("\n")
        for i in range(max(len(want), len(got))):
            w = want[i] if i < len(want) else "<missing>"
            g = got[i] if i < len(got) else "<missing>"
            if w != g:
                problems.append(f"    line {i + 1}: expected {w!r}")
                problems.append(f"              found    {g!r}")
    return problems


# --- Bifrost glyph roles: the surfaces must assign the same meanings ----------
#
# The §1 glyph table exists three times — as a markdown table in the spec, as an
# HTML table on the published page, and abbreviated in the CLAUDE.md §H backbone
# line. The sweep check above proves the copies agree on the glyphs' ORDER; this
# proves they agree on what the glyphs MEAN, which is the part that actually
# decided wrong: `@` read "signage" on the page for a full pass after the spec had
# reassigned it to "source", and nothing noticed, because no check compared them.
#
# Deliberately narrow: it compares the FIRST word of each archetype, lowercased.
# That catches a role REASSIGNMENT (`source`→`signage`, `cargo`→`payloads`,
# `cars`→`instantiators`) while tolerating the presentational differences the
# surfaces are entitled to — the spec says "Sanity / Tollbooth" where the page says
# "Sanity", and neither is wrong. A check that failed on phrasing would be turned
# off within a week, and an off check is worse than a narrow one.
GLYPH_HTML = re.compile(
    r'<td class="glyph">(.*?)</td>.*?<td class="arch">(.*?)</td>', re.S
)
# Presentational synonyms — the same role under two house names, not two roles.
# Keep this map SMALL and explicit; every entry is a place drift could hide.
ROLE_ALIAS = {"repo": "repository", "compliance": "weigh"}

GLYPH_SURFACES = [
    "04-user-services/ai-orchestration/highway-notation.md",  # canonical
    "docs/bifrost.html",
]


# Inline prose writes the descriptor glyph as ``` `` ` `` ``` — a backtick fenced by
# double backticks. No "grab what's between backticks" pattern survives that, so it is
# swapped for a sentinel before parsing and swapped back after. Without this the glyph
# is not compared anywhere, which reads as a pass.
GRAVE = "\x00GRAVE\x00"


def degrave(line):
    return line.replace("`` ` ``", f"`{GRAVE}`")


def norm_glyph(g):
    g = re.sub(r"<[^>]+>", "", g).replace("&nbsp;", "").replace("&amp;", "&")
    if GRAVE in g:
        return "`"
    # The descriptor glyph IS a backtick, so it is written `` ` `` in markdown and
    # would vanish under a blanket backtick strip — dropping the row silently, which
    # is the one outcome a drift check must never produce.
    if g.strip() and not g.strip("` \t"):
        return "`"
    return g.replace("`", "").strip()


def md_glyph_table(text):
    """Parse §1's table only.

    Scoped to the section because §3's soft-helper table is also a pipe table, with a
    different shape — a looser matcher happily reads its rows as glyph definitions. The
    §1 table is the five-column one: key | glyph | phase | archetype | meaning.
    """
    start = text.find("## 1. The backbone")
    if start < 0:
        return {}
    end = text.find("\n## ", start + 1)
    section = text[start: end if end > 0 else len(text)]

    table = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        glyph, archetype = norm_glyph(cells[1]), norm_role(cells[3])
        if not glyph or not archetype or archetype in ("archetype", "---", ":--"):
            continue
        table[glyph] = archetype
    return table


def norm_role(r):
    r = re.sub(r"<[^>]+>", "", r).strip().lower()
    first = re.split(r"[\s/(]+", r)[0] if r else ""
    return ROLE_ALIAS.get(first, first)


def check_glyph_roles():
    problems, tables = [], {}

    src = os.path.join(ROOT, GLYPH_SURFACES[0])
    if not os.path.exists(src):
        return [f"{GLYPH_SURFACES[0]}: missing (expected to carry the §1 glyph table)"]
    tables[GLYPH_SURFACES[0]] = md_glyph_table(open(src, encoding="utf-8").read())

    page = os.path.join(ROOT, GLYPH_SURFACES[1])
    if os.path.exists(page):
        tables[GLYPH_SURFACES[1]] = {
            norm_glyph(g): norm_role(a)
            for g, a in GLYPH_HTML.findall(open(page, encoding="utf-8").read())
        }

    # CLAUDE.md §H states the same assignments inline, abbreviated.
    brief = os.path.join(ROOT, "CLAUDE.md")
    if os.path.exists(brief):
        m = re.search(r"- \*\*Backbone:\*\*(.*?)(?=\n- \*\*)", open(brief, encoding="utf-8").read(), re.S)
        if m:
            # FIRST occurrence wins. The backbone line names each glyph once to assign
            # its role, then may name it again in a trailing aside ("Off-row `'`/`~`/
            # `` ` `` stage; keys 1-4 Preload ..."). Last-wins reads that aside as the
            # role and reports drift that is not there.
            brief = {}
            for g, role in re.findall(
                r"`{1,2}([^`]+)`{1,2}\s+([a-z][a-z/-]*)", degrave(m.group(1))
            ):
                brief.setdefault(norm_glyph(g), norm_role(role))
            tables["CLAUDE.md §H"] = brief

    canon_name = GLYPH_SURFACES[0]
    canon = tables.get(canon_name, {})
    if len(canon) < 8:
        return [f"{canon_name}: parsed only {len(canon)} glyph rows — the §1 table shape changed"]

    for name, table in tables.items():
        if name == canon_name:
            continue
        for glyph in sorted(set(canon) & set(table)):
            if canon[glyph] != table[glyph]:
                problems.append(
                    f"glyph {glyph!r}: {canon_name} says {canon[glyph]!r}, "
                    f"{name} says {table[glyph]!r}"
                )
        for glyph in sorted(set(canon) - set(table)):
            problems.append(f"glyph {glyph!r}: defined in {canon_name}, absent from {name}")
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
    sweep_problems = check_bifrost_sweep()
    if sweep_problems:
        failed = True
        print("FAIL Bifrost sweep string (bare `'` reference call)")
        for p in sweep_problems:
            print(f"  - {p}")
    else:
        print(f"ok   Bifrost sweep string identical across {len(SWEEP_FILES)} surfaces")

    glyph_problems = check_glyph_roles()
    if glyph_problems:
        failed = True
        print("FAIL Bifrost glyph roles disagree across surfaces")
        for p in glyph_problems:
            print(f"  - {p}")
    else:
        print("ok   Bifrost glyph roles agree across spec, page, and CLAUDE.md §H")

    if failed:
        print("\nDoc check FAILED")
        sys.exit(1)
    print(f"\nAll {len(md)} docs: links + repo-path references resolve.")


if __name__ == "__main__":
    main()
