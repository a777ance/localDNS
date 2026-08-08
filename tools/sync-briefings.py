#!/usr/bin/env python3
"""Render the canonical portfolio blocks into every A777ance repo's CLAUDE.md.

WHY THIS EXISTS (docs/architecture/warrant-sites.md)
----------------------------------------------------
Some rules are declared to hold in *every* repo, so every repo's CLAUDE.md carries a copy
of them. That makes each such rule a dozen hand-maintained files that are required to
agree — and git cannot help, because git only conflicts when two sessions touch the *same*
file. These are *different* files with an agreement obligation, so two parallel sessions
can each run green checks, each push cleanly, and still leave the portfolio
self-contradictory. That is not hypothetical: when `'` (Ignition) landed in localDNS, nine
sibling briefings silently kept describing a schema without it, and every one of them
individually looked fine.

The rules were already written down. Writing them down did nothing — they had an author
and no site. So the copies stop being copies: this script generates them, and `--check`
refuses a commit that would ship drift.

WHAT IS SYNCED
--------------
    bifrost             the command schema (canonical: ai-orchestration/briefing-block.md)
    branch-policy       Yggdrasil / Well of Mimir (ai-orchestration/branch-policy-block.md)
    proxy-doctrine      what actually refuses vs. only asks (ai-orchestration/proxy-block.md)
    session-visibility  the sibling-session grant (ai-orchestration/session-visibility-block.md)

All are portfolio-wide by declaration, and they failed differently. Bifrost DRIFTED —
nine briefings kept describing a schema without Ignition. Branch policy was ABSENT from
eight of ten, and absence is worse: a session reading a briefing that says nothing about
branching invents an answer, and the invented answer cut 337 stale branches. Silence is an
assignment, so every briefing states the rule.

Session visibility fails a third way, and it is the reason `check_session_grant` exists: the
block is *true prose about somewhere else*. A briefing cannot pre-approve a tool call — the
permission prompt never reads CLAUDE.md — so the sentence "this is granted" is only true if
`.claude/settings.json` carries it. Stating it without checking would make the briefing
confidently wrong, which is worse than silent.

USAGE
-----
    python3 tools/sync-briefings.py            # report drift (same as --check)
    python3 tools/sync-briefings.py --write    # render the canonical blocks everywhere
    python3 tools/sync-briefings.py --root DIR # portfolio root (default: parent of repo)
    python3 tools/sync-briefings.py --block X  # limit to one block (default: all)

EXIT CODES
----------
    0  every discovered briefing matches canonical
    1  drift found (or a repo carries a block not at all)
    2  a canonical source itself is missing/malformed

Repos that are not checked out are skipped, not failed — a session may hold only some of
the portfolio. The skip list is printed so a green run never silently means "checked
nothing."
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# localDNS carries the *long* form of both blocks in its own CLAUDE.md (§H, §3) rather
# than the condensed render. It is not a render target, but its long form must still
# agree with canonical — see check_backbone() and check_policy().
SELF = "localDNS"


@dataclasses.dataclass(frozen=True)
class Block:
    """One canonical block rendered into every sibling briefing."""

    name: str
    canonical: pathlib.Path
    marker: str            # marker stem, e.g. "bifrost-briefing"
    heading: str           # the section heading it lives under in a sibling briefing
    legacy_start: str      # bounds of an unmarked hand-written copy, so --write adopts it
    legacy_end: str

    @property
    def start(self) -> str:
        return f"<!-- {self.marker}:start"

    @property
    def end(self) -> str:
        return f"<!-- {self.marker}:end -->"

    @property
    def note(self) -> str:
        return (
            f"<!-- {self.marker}:start — GENERATED from "
            f"localDNS/{self.canonical.relative_to(REPO_ROOT).as_posix()} "
            f"by tools/sync-briefings.py. Do not hand-edit; edit the canonical file "
            f"and re-run. -->"
        )


BLOCKS = [
    Block(
        name="bifrost",
        canonical=REPO_ROOT / "04-user-services/ai-orchestration/briefing-block.md",
        marker="bifrost-briefing",
        heading="## Bifrost — active command schema (loads every session)",
        legacy_start="**Bifrost** is the A777ance command-composition schema",
        legacy_end="· rendered page: <https://a777ance.github.io/localDNS/bifrost.html>",
    ),
    Block(
        name="branch-policy",
        canonical=REPO_ROOT / "04-user-services/ai-orchestration/branch-policy-block.md",
        marker="branch-policy",
        heading="## Branch policy — Yggdrasil and the Well of Mimir",
        # No legacy unmarked form exists: the predecessor rule was a bullet inside a
        # repo-specific list, not a block, and is retired by hand in the same commit.
        legacy_start="\x00no-legacy\x00",
        legacy_end="\x00no-legacy\x00",
    ),
    Block(
        name="proxy-doctrine",
        canonical=REPO_ROOT / "04-user-services/ai-orchestration/proxy-block.md",
        marker="proxy-doctrine",
        heading="## Proxies — what actually refuses, and what only asks",
        # No legacy unmarked form: the doctrine is new (2026-08-08), so there is no
        # hand-written predecessor for --write to adopt.
        legacy_start="\x00no-legacy\x00",
        legacy_end="\x00no-legacy\x00",
    ),
    Block(
        name="session-visibility",
        canonical=REPO_ROOT / "04-user-services/ai-orchestration/session-visibility-block.md",
        marker="session-visibility",
        heading="## Session visibility — every session may see its siblings",
        legacy_start="\x00no-legacy\x00",
        legacy_end="\x00no-legacy\x00",
    ),
]

BACKBONE_RE = re.compile(r"- \*\*Backbone:\*\*(.*?)(?=\n- \*\*|\n\n)", re.S)
# One "`glyph` role-word" pair, e.g. "`@` source" — role is the first word after the glyph.
PAIR_RE = re.compile(r"`{1,2}([^`]+)`{1,2}\s+([a-z][a-z-]*)")

# The retired directive, in the two bolded forms it actually shipped in. Deliberately
# narrow: the *quoted* historical reference ("superseding \"push to `main`, no branches\"")
# appears in the new text by design and must not trip this. A check that failed on
# phrasing would be switched off, and an off check is worse than a narrow one.
LEGACY_DIRECTIVE_RE = re.compile(r"\*\*Push to `main`, no branch(es|ing)")


def read_canonical(block: Block) -> str:
    if not block.canonical.exists():
        sys.exit(f"FATAL canonical block missing: {block.canonical}")
    text = block.canonical.read_text(encoding="utf-8")
    i, j = text.find(f"<!-- {block.marker}:start -->"), text.find(block.end)
    if i < 0 or j < 0 or j < i:
        sys.exit(f"FATAL canonical block has no start/end marker pair: {block.canonical}")
    return text[i + len(f"<!-- {block.marker}:start -->"):j].strip("\n")


def discover(root: pathlib.Path) -> list[pathlib.Path]:
    """Every sibling git repo carrying a CLAUDE.md, localDNS excluded."""
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name == SELF or not (d / ".git").exists():
            continue
        if (d / "CLAUDE.md").exists():
            out.append(d / "CLAUDE.md")
    return out


def extract(text: str, block: Block) -> tuple[str | None, int, int, bool]:
    """Return (current_block, span_start, span_end, is_marked).

    `is_marked` distinguishes a generated block from a legacy hand-written one whose
    content happens to match. A legacy copy is still drift: it is not addressed by the
    generator, so the next canonical edit would leave it behind exactly the way Ignition
    did. Matching content today is not the same as being wired to the source.
    """
    i = text.find(block.start)
    if i >= 0:
        head_end = text.find("-->", i)
        j = text.find(block.end, i)
        if head_end >= 0 and j >= 0:
            return text[head_end + 3:j].strip("\n"), i, j + len(block.end), True
    i = text.find(block.legacy_start)
    if i >= 0:
        j = text.find(block.legacy_end, i)
        if j >= 0:
            return text[i:j + len(block.legacy_end)], i, j + len(block.legacy_end), False
    return None, -1, -1, False


def render(text: str, block: Block, body: str) -> str:
    """Splice the canonical block in, adopting a legacy copy or creating the section."""
    marked = f"{block.note}\n\n{body}\n\n{block.end}"
    _, s, e, _ = extract(text, block)
    if s >= 0:
        return text[:s] + marked + text[e:]
    if block.heading in text:  # heading present, body missing
        return text.replace(block.heading, f"{block.heading}\n\n{marked}", 1)
    sep = "" if text.endswith("\n") else "\n"
    return f"{text}{sep}\n---\n\n{block.heading}\n\n{marked}\n"


def pairs(line: str) -> dict[str, str]:
    """Glyph -> role from a Backbone line, first occurrence winning.

    Two parsing hazards, both of which silently *weaken* the check rather than break
    it — the dangerous direction:
      * The descriptor glyph is written ``` `` ` `` ```; no backtick-delimited pattern
        survives it, so it is swapped for a sentinel and back.
      * Each glyph is named once to assign its role and may be named again in the
        trailing aside ("Off-row `'`/`~`/`` ` `` stage"). Last-wins reads the aside as
        the role.
    """
    line = line.replace("`` ` ``", "`\x00GRAVE\x00`")
    out: dict[str, str] = {}
    for g, role in PAIR_RE.findall(line):
        g = "`" if "\x00GRAVE\x00" in g else g.strip()
        out.setdefault(g, role)
    return out


def check_backbone(body: str) -> list[str]:
    """The condensed block and localDNS §H are separate artifacts by design; the one thing
    that must never diverge is which glyph means what."""
    self_md = REPO_ROOT / "CLAUDE.md"
    if not self_md.exists():
        return []
    a = BACKBONE_RE.search(body)
    b = BACKBONE_RE.search(self_md.read_text(encoding="utf-8"))
    if not a or not b:
        return ["could not locate a Backbone line in the block and/or localDNS CLAUDE.md §H"]
    pa, pb = pairs(a.group(1)), pairs(b.group(1))
    return [
        f"glyph {g!r}: briefing-block says {pa[g]!r}, localDNS CLAUDE.md §H says {pb[g]!r}"
        for g in sorted(pa.keys() & pb.keys()) if pa[g] != pb[g]
    ]


def check_policy(targets: list[pathlib.Path]) -> list[str]:
    """No briefing may still carry the retired push-to-main directive, and localDNS's own
    long form must name the working branch.

    The condensed block is generated, so drift in *it* is already caught. What this adds is
    the half a generator cannot see: a repo-specific rule elsewhere in the same file that
    still says the opposite. customers/CLAUDE.md stated the old rule in its own §1 list —
    nowhere near the synced section — and a file that contradicts itself teaches the
    contradiction to whichever session reads that section first.
    """
    problems = []
    for path in [REPO_ROOT / "CLAUDE.md", *targets]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if LEGACY_DIRECTIVE_RE.search(text):
            problems.append(
                f"{path.parent.name}/CLAUDE.md still carries the retired "
                f'"Push to `main`, no branches" directive'
            )
    self_md = REPO_ROOT / "CLAUDE.md"
    if self_md.exists():
        text = self_md.read_text(encoding="utf-8")
        if "Yggdrasil" not in text:
            problems.append("localDNS/CLAUDE.md §3 does not name Yggdrasil as the working branch")
    return problems


def check_session_grant(targets: list[pathlib.Path]) -> list[str]:
    """The session-visibility block *claims* the grant lives in `.claude/settings.json`.

    A briefing cannot pre-approve a tool call — the permission prompt does not read
    CLAUDE.md — so that sentence is only true if the settings file actually carries it.
    Left unchecked it is the exact failure this repo keeps finding: a rule with an author
    and no site, believed because it is written down. So the claim is verified against the
    file that decides.
    """
    required = {f"mcp__{s}__{t}"
                for s in ("Claude_Code_Remote", "claude-code-remote")
                for t in ("list_sessions", "get_session", "create_session")}
    problems = []
    for repo in [REPO_ROOT, *[t.parent for t in targets]]:
        settings = repo / ".claude" / "settings.json"
        if not settings.exists():
            problems.append(f"{repo.name}: no .claude/settings.json to carry the session grant")
            continue
        try:
            allow = set(json.loads(settings.read_text(encoding="utf-8"))
                        .get("permissions", {}).get("allow", []))
        except (json.JSONDecodeError, OSError) as exc:
            problems.append(f"{repo.name}/.claude/settings.json unreadable: {exc}")
            continue
        # Either server spelling satisfies a given tool; only a tool missing under BOTH
        # spellings is a real gap.
        for tool in ("list_sessions", "get_session", "create_session"):
            if not any(f"mcp__{s}__{tool}" in allow
                       for s in ("Claude_Code_Remote", "claude-code-remote")):
                problems.append(
                    f"{repo.name}/.claude/settings.json does not grant {tool} — the "
                    f"session-visibility block says it does")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="render the blocks (default: check only)")
    ap.add_argument("--root", type=pathlib.Path, default=REPO_ROOT.parent,
                    help="portfolio root holding the sibling repos")
    ap.add_argument("--block", choices=[b.name for b in BLOCKS],
                    help="limit to one block (default: all)")
    args = ap.parse_args()

    blocks = [b for b in BLOCKS if not args.block or b.name == args.block]
    bodies = {b.name: read_canonical(b) for b in blocks}
    targets = discover(args.root)
    if not targets:
        print(f"note  no sibling repos found under {args.root} — nothing to check")

    drift, wrote, ok = [], [], []
    for path in targets:
        touched = stale = False
        for block in blocks:
            text = path.read_text(encoding="utf-8")
            body = bodies[block.name]
            current, _, _, is_marked = extract(text, block)
            if current == body and is_marked:
                continue
            if args.write:
                path.write_text(render(text, block, body), encoding="utf-8")
                touched = True
            else:
                stale = True
                if current is None:
                    why = f"no {block.name} block found"
                elif current != body:
                    why = f"{block.name} block differs from canonical"
                else:
                    why = (f"{block.name} block is unmarked — not wired to the generator "
                           f"(one-time migration)")
                drift.append(f"{path.parent.name}/CLAUDE.md: {why}")
        # A repo with any stale block is not "ok" — reporting both would let a reader
        # skim the ok list and miss the failure it contradicts.
        if stale:
            continue
        (wrote if touched else ok).append(path.parent.name)

    problems = [f"[{b.name}] {p}" for b in blocks if b.name == "bifrost"
                for p in check_backbone(bodies["bifrost"])]
    if any(b.name == "branch-policy" for b in blocks):
        problems += [f"[branch-policy] {p}" for p in check_policy(targets)]
    if any(b.name == "session-visibility" for b in blocks):
        problems += [f"[session-visibility] {p}" for p in check_session_grant(targets)]

    for name in wrote:
        print(f"sync {name}")
    for name in ok:
        print(f"ok   {name}")
    if problems:
        print("\nFAIL portfolio invariants disagree between the two briefing tiers")
        for p in problems:
            print(f"     {p}")
    if drift:
        print("\nFAIL a canonical block drifted")
        for d in drift:
            print(f"     {d}")
        print("\n     Fix: python3 tools/sync-briefings.py --write")
    if not drift and not problems:
        names = ", ".join(b.name for b in blocks)
        verb = "synced" if wrote else "match"
        print(f"\nAll {len(ok) + len(wrote)} briefings {verb} canonical ({names}); "
              f"cross-tier invariants agree.")
    return 1 if (drift or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
