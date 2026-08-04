#!/usr/bin/env python3
"""Bifrost — parse + score. Stages 1 and 2 of the dispatcher.

Implements the two pure, offline-testable stages of the Bifrost notation
(canonical spec: ../highway-notation.md):

  PARSE  a glyph string -> an ordered list of Segments
  SCORE  those segments -> a Kendall tau turbulence score + band

Stage 3 (ROUTE) is deliberately NOT here. Routing dispatches to slash
commands and repos, and a supervisor already does that on the live t630
without being snapshotted into this repo. Writing a second router from the
spec would put a plausible fiction in a rollback target. Route lands when
it can be read off the machine.

Standard library only. No side effects — parse() and score() are pure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional

__all__ = [
    "Segment", "Pipeline", "Turbulence",
    "parse", "score", "GOLDEN_RULE", "BACKBONE", "STAGING",
]


# --- the glyph table (spec §1) -------------------------------------------
#
# The Golden Rule is the number row swept left->right with Shift held. Rank
# is position in that sweep; the Kendall tau score in score() counts
# inversions against it.

GOLDEN_RULE = "!@#$%^&*()"

BACKBONE = {
    "!": (1, "Payloads",      "Preload"),
    "@": (2, "Signage",       "Preload"),
    "#": (3, "Repository",    "Preload"),
    "$": (4, "Sanity",        "Preload"),
    "%": (5, "WeighStation",  "Gateway"),
    "^": (6, "Instantiators", "Travel"),
    "&": (7, "Rotary",        "Travel"),
    "*": (8, "TrafficLight",  "Travel"),
    "(": (9, "Intersection",  "Travel"),
    ")": (10, "Intersection", "Travel"),
}

# Off-row staging glyphs. They carry no Golden Rule rank, so they take no
# part in the inversion count -- see score() for why that matters.
STAGING = {
    "~": "Continuity",
    "`": "Descriptor",
}

# Soft helpers (spec §3): "glow-in-the-dark road lines", not hard syntax.
# They are stripped before lexing -- dropping them must not change meaning.
SOFT_HELPERS = set("<>?{}[]\"':;")

_GLYPHS = set(BACKBONE) | set(STAGING)

# A /how slash command: /render, /usage, /check-docs
_SLASH = re.compile(r"/[A-Za-z][A-Za-z0-9_-]*")


@dataclass
class Segment:
    """One archetype slot: the glyph, how it's fulfilled, and the specifics."""

    glyph: str
    archetype: str
    rank: Optional[int]        # Golden Rule rank; None for staging glyphs
    phase: str
    intensity: int = 1         # $$$$ or $+++ -> 4. Never affects the score.
    stress: int = 0            # $--- -> 3. Adversarial fault injection.
    commands: List[str] = field(default_factory=list)
    prompt: str = ""

    @property
    def is_staging(self) -> bool:
        return self.rank is None


@dataclass
class Pipeline:
    segments: List[Segment]
    source: str

    @property
    def backbone(self) -> List[Segment]:
        """Ranked segments only, in order of appearance."""
        return [s for s in self.segments if not s.is_staging]


@dataclass
class Turbulence:
    kendall_tau: int
    band: str
    label: str
    panic: bool                # True at MASH: abort, intervene like a human


# --- stage 1: PARSE -------------------------------------------------------

def _descriptor_spans(text: str) -> dict[int, int]:
    """Map each opening backtick offset -> its closing backtick offset.

    The backtick is a staging glyph that both opens and closes a descriptor
    (spec §2), so the contents are prose, not notation. Anything glyph-like
    inside -- a `#` in a repo name, a `$` in a shell snippet -- must not open
    a segment. The lexer consumes a whole span as one Descriptor and resumes
    after the closing backtick.

    NOTE (spec gap): a descriptor span is the ONLY masking the notation
    supports. There is no general escape for a literal glyph in ordinary
    sub-prompt text -- see the README. Rather than invent one, an unbalanced
    backtick is treated as a bare glyph and the text after it lexes normally.
    """
    spans: dict[int, int] = {}
    i, n = 0, len(text)
    while i < n:
        if text[i] == "`":
            close = text.find("`", i + 1)
            if close == -1:
                break                      # unbalanced: leave the rest alone
            spans[i] = close
            i = close + 1
        else:
            i += 1
    return spans


def _split_commands(body: str) -> tuple[List[str], str]:
    """Pull leading /how slash commands off a segment body."""
    commands: List[str] = []
    rest = body.lstrip()
    while True:
        m = _SLASH.match(rest)
        if not m:
            break
        commands.append(m.group(0))
        rest = rest[m.end():].lstrip()
    return commands, rest.strip()


def parse(text: str) -> Pipeline:
    """Lex a Bifrost string into ordered Segments.

    Split-on-glyph, not a grammar: each backbone or staging glyph opens a
    segment that runs to the next glyph. Adjacent repeats of the same glyph
    and any trailing +/- collapse into one node carrying intensity/stress.
    """
    spans = _descriptor_spans(text)
    segments: List[Segment] = []

    i, n = 0, len(text)
    while i < n:
        ch = text[i]

        # a descriptor consumes its whole span as one Segment
        if ch == "`" and i in spans:
            close = spans[i]
            segments.append(Segment(
                glyph="`",
                archetype=STAGING["`"],
                rank=None,
                phase="Staging",
                prompt=text[i + 1:close].strip(),
            ))
            i = close + 1
            continue

        if ch not in _GLYPHS:
            i += 1
            continue

        # collapse an adjacent run of the identical glyph: $$$$ -> intensity 4
        run = 1
        j = i + 1
        while j < n and text[j] == ch:
            run += 1
            j += 1

        # trailing +/- modifiers: $+++ -> intensity 4, $--- -> stress 3
        plus = minus = 0
        while j < n and text[j] in "+-":
            if text[j] == "+":
                plus += 1
            else:
                minus += 1
            j += 1

        # body runs to the next glyph, stopping at a descriptor's opening tick
        k = j
        while k < n and text[k] not in _GLYPHS:
            k += 1

        body = "".join(c for c in text[j:k] if c not in SOFT_HELPERS)
        commands, prompt = _split_commands(body)

        if ch in BACKBONE:
            rank, archetype, phase = BACKBONE[ch]
        else:
            rank, archetype, phase = None, STAGING[ch], "Staging"

        segments.append(Segment(
            glyph=ch,
            archetype=archetype,
            rank=rank,
            phase=phase,
            intensity=run + plus,
            stress=minus,
            commands=commands,
            prompt=prompt,
        ))
        i = k

    return Pipeline(segments=segments, source=text)


# --- stage 2: SCORE -------------------------------------------------------

# spec §5
_BANDS = (
    (0,  0,             "Straightaway",      "perfect order; standard"),
    (1,  5,             "Scenic Route",      "deliberate weaving; customized physics"),
    (6,  15,            "Spaghetti Junction", "computationally dense; heavy nested logic"),
    (16, float("inf"),  "MASH",              "keyboard-smash, not a road; panic-abort"),
)


def score(pipeline: Pipeline) -> Turbulence:
    """Kendall tau distance from the Golden Rule: K = sum_{i<j} I(v_i > v_j).

    Two normalizations make this measure ORDER and nothing else:

    1. Staging glyphs (~, `) are excluded. They sit off the number row and
       have no Golden Rule rank, so they cannot be out of order with respect
       to it. Counting them would score a legal lazy anchor as turbulence.

    2. Intensity is already collapsed by parse(): $$$$ is one node, not four.
       Without that, an emphatic-but-perfectly-ordered string accumulates
       inversions purely from repetition and can cross into MASH -- a panic
       abort triggered by the user pressing harder on a guardrail, which is
       precisely backwards.

    n is a dozen glyphs at most, so the naive O(n^2) double loop is correct
    and instant. Kendall tau does not need to be clever here.
    """
    ranks = [s.rank for s in pipeline.backbone if s.rank is not None]

    k = 0
    for a in range(len(ranks)):
        for b in range(a + 1, len(ranks)):
            if ranks[a] > ranks[b]:
                k += 1

    for lo, hi, label, note in _BANDS:
        if lo <= k <= hi:
            return Turbulence(
                kendall_tau=k,
                band=label,
                label=note,
                panic=(label == "MASH"),
            )
    raise AssertionError("unreachable: bands cover all k >= 0")


# --- CLI ------------------------------------------------------------------

def _render(pipeline: Pipeline, turb: Turbulence) -> str:
    lines = [f"source   {pipeline.source}", ""]
    for s in pipeline.segments:
        rank = "  -" if s.rank is None else f"{s.rank:3d}"
        mods = []
        if s.intensity > 1:
            mods.append(f"intensity={s.intensity}")
        if s.stress:
            mods.append(f"stress={s.stress}")
        cmds = " ".join(s.commands)
        lines.append(
            f"  {s.glyph}  rank {rank}  {s.archetype:<14} "
            f"{cmds:<22} {s.prompt[:38]:<38} {' '.join(mods)}".rstrip()
        )
    lines += [
        "",
        f"kendall tau  {turb.kendall_tau}",
        f"turbulence   {turb.band} — {turb.label}",
    ]
    if turb.panic:
        lines.append("PANIC        drop payloads; respond with human intervention, not a syntax error")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bifrost",
        description="Parse and score a Bifrost notation string (spec: ../highway-notation.md)",
    )
    ap.add_argument("string", help="the Bifrost string to analyze")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)

    pipeline = parse(args.string)
    turb = score(pipeline)

    if args.json:
        payload = {
            "source": pipeline.source,
            "segments": [
                {k: v for k, v in asdict(s).items() if not k.startswith("_")}
                for s in pipeline.segments
            ],
            "turbulence": asdict(turb),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(_render(pipeline, turb))

    # MASH is a panic-abort, and the exit code should say so.
    return 2 if turb.panic else 0


if __name__ == "__main__":
    sys.exit(main())
