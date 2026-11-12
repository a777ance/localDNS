#!/usr/bin/env python3
"""check-statements.py — gate for the honesty rule on customer Statements.

The rule (CLAUDE.md, "Honesty of the kept document"): a Statement prints only numbers
the box measured; with no measured volume the category breakdown is omitted, not faked.

Imports docs/statements/tools/compose.py by path and asserts, on synthetic inputs built
here (no files, no box, no real customer data):
  1. build_alloc: every percentage is between 0 and 100, the rows sum to between 98
     and 102, and the total equals the sum of the input bytes;
  2. build_alloc: no row names a category that was not in its input, other than a
     single "Other" row;
  3. compose(stats, sidecar) with no measured volume (by_category empty, missing,
     null, or all zero) returns no category allocation, no profile or comparison
     built from one, and no gigabyte figure anywhere in its output, even when the
     sidecar carries a forced archetype and a complete cohort.

Not covered: compose.main() (file reading and writing) and the HTML that
generate_client.py renders from this output.

Known faults in compose.py are pinned in KNOWN below: each is reported on every run
and does not fail the gate, but the gate fails if a pinned fault stops reproducing,
so the pin cannot outlive the fault.
Exit 0 when clean, 1 otherwise.
"""
import importlib.util
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "docs/statements/tools/compose.py"
GB = 1024 ** 3
GIGABYTES = re.compile(r"\bGB\b|gigabyte", re.IGNORECASE)
VOLUME_KEYS = ("alloc", "total_gb", "compare", "cohort", "arch_name", "arch_tag", "arch_body",
               "chips", "macro_line", "emoji", "sug_title", "suggestions", "affirmation")


def load_compose():
    spec = importlib.util.spec_from_file_location("statement_compose", COMPOSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def alloc_problems(mod, by_category):
    """The faults build_alloc shows on one input, as a list of strings."""
    out = []
    rows, total = mod.build_alloc(dict(by_category))
    for name, pct, _label in rows:
        if not 0 <= pct <= 100:
            out.append(f"percentage {pct} for {name!r} is outside 0 to 100")
    pct_sum = sum(r[1] for r in rows)
    if not 98 <= pct_sum <= 102:
        out.append(f"percentages sum to {pct_sum}, outside 98 to 102")
    if total != sum(by_category.values()):
        out.append(f"total {total} is not the sum of the input bytes {sum(by_category.values())}")
    names = [r[0] for r in rows]
    for name in names:
        if name != "Other" and name not in by_category:
            out.append(f"row {name!r} was not in the input")
    if names.count("Other") > 1:
        out.append(f"{names.count('Other')} 'Other' rows")
    if len(set(names)) != len(names):
        out.append("a category appears in more than one row")
    return out


def alloc_inputs():
    """Named synthetic traffic mixes: (label, {category: bytes})."""
    cases = [
        ("one category", {"Streaming & Video": 40 * GB}),
        ("two categories", {"Streaming & Video": 30 * GB, "Gaming": 10 * GB}),
        ("six categories", {f"Cat {i}": (i + 1) * GB for i in range(6)}),
        ("seven equal categories", {f"Cat {i}": 5 * GB for i in range(7)}),
        ("twelve categories", {f"Cat {i}": (i + 1) * 3 * GB for i in range(12)}),
        ("Other measured, largest", {"Other": 50 * GB, "Gaming": 20 * GB, "Social": 5 * GB}),
        ("Other measured, smallest of nine", {**{f"Cat {i}": (i + 2) * GB for i in range(8)}, "Other": GB}),
        ("a zero-byte category", {"Streaming & Video": 12 * GB, "Gaming": 0}),
        ("tiny volumes", {"Streaming & Video": 3, "Gaming": 2, "Social": 1}),
    ]
    rng = random.Random(777)  # fixed seed: the same inputs on every run
    for n in range(200):
        size = rng.randint(1, 14)
        mix = {f"Cat {i}": rng.randint(1, 400 * GB) for i in range(size)}
        if rng.random() < 0.3:
            mix["Other"] = rng.randint(1, 400 * GB)
        cases.append((f"random mix {n}", mix))
    return cases


# Faults found in compose.py and reported, not fixed here. (label, input, text expected in the fault)
KNOWN = [
    ("rounding ties: six categories at 14.5% and a 13% remainder",
     {**{f"Cat {i}": 145 for i in range(6)}, "Cat 6": 130}, "percentages sum to 97"),
    ("rounding ties: six categories at 15.5% and a 7% remainder",
     {**{f"Cat {i}": 155 for i in range(6)}, "Cat 6": 70}, "percentages sum to 103"),
    ("empty input: total is reported as 1 byte, not 0",
     {}, "total 1 is not the sum"),
]


def base_stats():
    return {
        "queries": {"total": 120000, "blocked": 18000},
        "uptime": {"pct": 99.9},
        "latency_ms": {"peak": 31},
        "vpn_sessions": {"count": 4},
        "devices": 14,
    }


def tempting_sidecar():
    """A sidecar that offers compose every chance to print volume it does not have."""
    return {
        "account": {"holder": "Synthetic Household", "acct": "TEST-0000", "period": "Test period",
                    "stmt_date": "2000-01-01", "live_url": "https://example.invalid/live",
                    "stmt_url": "https://example.invalid/stmt"},
        "handled": [], "handled_foot": "",
        "force_archetype": "prime-time",
        "cohort": {"label": "Synthetic cohort", "avg_daily_gb": 9.5, "avg_threats_day": 400,
                   "avg_latency_ms": 40},
    }


def no_volume_stats():
    cases = []
    s = base_stats()
    cases.append(("volume missing", s))
    s = base_stats(); s["volume"] = {}
    cases.append(("by_category missing", s))
    s = base_stats(); s["volume"] = {"by_category": {}}
    cases.append(("by_category empty", s))
    s = base_stats(); s["volume"] = {"by_category": None}
    cases.append(("by_category null", s))
    s = base_stats(); s["volume"] = {"by_category": {"Streaming & Video": 0, "Gaming": 0}}
    cases.append(("by_category all zero", s))
    return cases


def main() -> int:
    mod = load_compose()
    problems, notes = [], []

    cases = alloc_inputs()
    for label, mix in cases:
        for p in alloc_problems(mod, mix):
            problems.append(f"build_alloc, {label}: {p}")

    for label, mix, expected in KNOWN:
        found = alloc_problems(mod, mix)
        if any(expected in p for p in found):
            notes.append(f"known fault in compose.py, reported and not fixed: {label}")
        else:
            problems.append(f"pinned fault no longer reproduces ({label}): remove it from KNOWN "
                            f"and move its input into alloc_inputs()")

    empties = no_volume_stats()
    for label, stats in empties:
        try:
            cfg, archetype = mod.compose(stats, tempting_sidecar())
        except Exception as e:  # a crash is a finding, not a broken gate
            problems.append(f"compose, {label}: raised {type(e).__name__}: {e}")
            continue
        for key in VOLUME_KEYS:
            if key in cfg:
                problems.append(f"compose, {label}: output carries {key!r} with no measured volume")
        if archetype != "no-volume":
            problems.append(f"compose, {label}: classified as {archetype!r} with no measured volume")
        text = json.dumps(cfg, ensure_ascii=False)
        hit = GIGABYTES.search(text)
        if hit:
            problems.append(f"compose, {label}: output has a gigabyte figure near "
                            f"{text[max(0, hit.start() - 30):hit.end()]!r}")
        if len(cfg.get("summary", [])) != 6:
            problems.append(f"compose, {label}: the measured Account Summary is not six rows")

    # The control: with measured volume the same call does print an allocation, so the
    # omissions above are the guard working and not a compose that never prints one.
    measured = base_stats()
    measured["volume"] = {"by_category": {"Streaming & Video": 30 * GB, "Gaming": 10 * GB}}
    cfg, _ = mod.compose(measured, tempting_sidecar())
    if "alloc" not in cfg or not GIGABYTES.search(json.dumps(cfg)):
        problems.append("compose, control: measured volume produced no allocation; the no-volume cases prove nothing")

    for p in problems:
        print("FAIL", p)
    for n in notes:
        print("note", n)
    if not problems:
        print(f"ok   build_alloc honest on {len(cases)} synthetic mixes; compose omits every "
              f"volume section on {len(empties)} no-volume inputs; {len(notes)} known faults pinned")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
