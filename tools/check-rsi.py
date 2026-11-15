#!/usr/bin/env python3
"""check-rsi.py — gate for RSI-OODA (docs/ai-cto/rsi/).

    python3 tools/check-rsi.py

Fails if:
  * 2 or fewer leans are open in docs/ai-cto/rsi/QUEUE.md (the refill rule: write 30 more first),
  * a lean id (L-NNN) is defined twice across QUEUE.md and docs/ai-cto/leans-harness.md,
  * a ledger row's pass has no docs/ai-cto/rsi/runs/pass-N.json, or the rows are not newest first,
  * "RSI" appears without "-OODA" in a doc outside the dated archives (the founder's naming rule).
Exit 0 when clean, 1 otherwise. Standard library only.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RSI = ROOT / "docs/ai-cto/rsi"
ARCHIVES = re.compile(r"handoff-\d{4}-\d{2}-\d{2}\.md$")
problems = []

queue = (RSI / "QUEUE.md").read_text(encoding="utf-8")
open_leans = re.findall(r"^- \[ \] \*\*(L-\d+)", queue, re.M)
if len(open_leans) <= 2:
    problems.append(f"only {len(open_leans)} lean(s) open in QUEUE.md: write 30 more before the next pass (refill rule)")

defined = []
for f in (RSI / "QUEUE.md", ROOT / "docs/ai-cto/leans-harness.md"):
    defined += re.findall(r"^- (?:\[[ x]\] )?\*\*(L-\d+[a-z]?) ·", f.read_text(encoding="utf-8"), re.M)
dups = sorted({d for d in defined if defined.count(d) > 1})
if dups:
    problems.append("lean id defined more than once: " + ", ".join(dups))

ledger = (RSI / "LEDGER.md").read_text(encoding="utf-8")
passes = [int(n) for n in re.findall(r"^\| (\d+) · ", ledger, re.M)]
if passes != sorted(passes, reverse=True):
    problems.append(f"ledger rows are not newest first: {passes}")
for n in passes:
    row = re.search(rf"^\| {n} · ([^|]*)\|", ledger, re.M).group(1)
    if "in flight" not in row and not (RSI / f"runs/pass-{n}.json").exists():
        problems.append(f"ledger pass {n} has no runs/pass-{n}.json")

for f in sorted((ROOT / "docs").rglob("*.md")):
    if ARCHIVES.search(f.name):
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(r"\bRSI\b(?!-OODA)", line):
            problems.append(f"{f.relative_to(ROOT)}:{i}: 'RSI' without '-OODA'")

for p in problems:
    print("FAIL", p)
print(f"{'FAILED' if problems else 'ok'}   RSI-OODA: {len(open_leans)} lean(s) open, {len(passes)} pass(es) in the ledger, {len(set(defined))} lean ids")
sys.exit(1 if problems else 0)
