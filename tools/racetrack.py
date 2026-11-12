#!/usr/bin/env python3
"""racetrack.py: score one racetrack mode folder (docs/ai-cto/fleet/racetrack/<MODE>/).

For every finding it checks the citations: each `path:line` or `path:start-end` must name a
real file and a line inside it. It reports bullets, citations, bad citations, the claimed
"Count:" against the real bullet count, and whether the mode wrote outside its own folder.

    python3 tools/racetrack.py MODE            score one mode and print the metrics
    python3 tools/racetrack.py --selftest      prove the scorer catches a bad citation

Exit 0 when every citation resolves and the counts match, 1 otherwise. Standard library only.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACK = ROOT / "docs/ai-cto/fleet/racetrack"
CITE = re.compile(r"((?:[\w.-]+/)*[\w.-]+\.\w+):(\d+)(?:-(\d+))?")
COUNT = re.compile(r"^Count:\s*(\d+)", re.MULTILINE)


def citations(text):
    """Every file:line citation in the findings text, as (path, start, end)."""
    for m in CITE.finditer(text):
        start = int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        yield m.group(1), start, end


HARNESS = {"tools/racetrack.py"}  # the scorer's own file: never counted against a run


def locate(path, root):
    """A citation with no directory is matched by name: it resolves only when exactly one tracked
    file has that name. Returns (file or None, reason when None)."""
    if "/" in path:
        f = root / path
        return (f if f.is_file() else None), f"no such file {path}"
    hits = [p for p in root.rglob(path) if ".git" not in p.parts and p.is_file()]
    if len(hits) == 1:
        return hits[0], ""
    return None, f"{len(hits)} files named {path}"


def resolve(path, start, end, root):
    """None if the citation resolves; otherwise the reason it does not."""
    f, why = locate(path, root)
    if f is None:
        return why
    n = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
    if start < 1 or end < start or end > n:
        return f"{path} has {n} lines; citation {start}-{end} is outside it"
    return None


def score(mode_dir, root=ROOT):
    findings = sorted(mode_dir.glob("*.md"))
    bullets = cites = bad = 0
    problems = []
    claimed = None
    for f in findings:
        text = f.read_text(encoding="utf-8")
        m = COUNT.search(text)
        claimed = (claimed or 0) + int(m.group(1)) if m else claimed
        if not m:
            problems.append(f"{f.name}: no Count: line")
        file_bullets = [ln for ln in text.splitlines() if ln.startswith("- ")]
        bullets += len(file_bullets)
        if m and int(m.group(1)) != len(file_bullets):
            problems.append(f"{f.name}: Count says {m.group(1)}, file has {len(file_bullets)} bullets")
        for path, s, e in citations(text):
            cites += 1
            why = resolve(path, s, e, root)
            if why:
                bad += 1
                problems.append(f"{f.name}: bad citation {path}:{s}-{e}: {why}")
    outside = []
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout
        outside = [ln[3:] for ln in out.splitlines()
                   if "docs/ai-cto/fleet/racetrack/" not in ln[3:] and ln.strip()
                   and ln[3:] not in HARNESS]
    except OSError:
        pass
    return {
        "files": len(findings), "bullets": bullets, "citations": cites,
        "bad_citations": bad, "claimed_count": claimed,
        "outside_write_area": outside, "problems": problems,
    }


def selftest():
    """A tiny fake repo: one good citation, one past the end of its file. The scorer must
    accept the first and reject the second."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "src.py").write_text("a\nb\nc\n")
        mode = root / "mode"
        mode.mkdir()
        (mode / "R1.md").write_text("Count: 2\n\n- src.py:2 good\n- src.py:9 past the end\n")
        r = score(mode, root)
        ok = r["bad_citations"] == 1 and r["citations"] == 2 and r["bullets"] == 2
        print(("ok   " if ok else "FAIL ") + f"selftest: 2 citations, {r['bad_citations']} bad (expected 1)")
        return 0 if ok else 1


def main(argv):
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__)
        return 2
    mode_dir = TRACK / argv[0]
    if not mode_dir.is_dir():
        print(f"FAILED: no mode folder {mode_dir}")
        return 2
    r = score(mode_dir)
    print(json.dumps({k: v for k, v in r.items() if k != "problems"}, indent=2))
    for p in r["problems"]:
        print("FAIL", p)
    return 1 if r["problems"] or r["outside_write_area"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
