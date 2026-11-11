#!/usr/bin/env python3
"""matrix.py — the Matrix's own tooling: one entry point, called as cardinal.method.

    python3 tools/matrix.py observe.read  PATH [START [END]]
    python3 tools/matrix.py observe.find  GLOB
    python3 tools/matrix.py observe.search PATTERN [PATH]
    python3 tools/matrix.py orient.ground
    python3 tools/matrix.py decide.gate
    python3 tools/matrix.py act.write PATH            (content on stdin; keeps a .bak)
    python3 tools/matrix.py act.edit  PATH OLD NEW    (OLD must occur exactly once)
    python3 tools/matrix.py list

These are the targets the native tools are repointed to (see "repoint" in
.claude/cardinal-map.json). Every call is appended to .claude/.matrix-log.
Paths are confined to the repository. Standard library only.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "node_modules", "__pycache__"}


def inside(p: str) -> Path:
    path = (ROOT / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    if ROOT != path and ROOT not in path.parents:
        sys.exit(f"FAILED: {p} is outside the repository")
    return path


def walk():
    for f in ROOT.rglob("*"):
        if f.is_file() and not (SKIP & set(f.relative_to(ROOT).parts)):
            yield f


def observe_read(path, start="1", end=None):
    lines = inside(path).read_text(encoding="utf-8", errors="replace").split("\n")
    a, b = int(start), int(end) if end else len(lines)
    for i, line in enumerate(lines[a - 1:b], a):
        print(f"{i:6}\t{line}")


def observe_find(glob):
    for f in sorted(ROOT.glob(glob)):
        if not (SKIP & set(f.relative_to(ROOT).parts)):
            print(f.relative_to(ROOT))


def observe_search(pattern, path="."):
    rx, base = re.compile(pattern), inside(path)
    files = [base] if base.is_file() else [f for f in walk() if base in f.parents or base == ROOT]
    for f in sorted(files):
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
                if rx.search(line):
                    print(f"{f.relative_to(ROOT)}:{i}:{line[:200]}")
        except (UnicodeDecodeError, OSError):
            continue


def orient_ground():
    for name in ("initiatives.md", "debt.md", "blocked.md"):
        print(f"== docs/ai-cto/{name}")
        for line in (ROOT / "docs/ai-cto" / name).read_text(encoding="utf-8").split("\n"):
            if line.startswith("## ") or line.startswith("- **DEC-"):
                print("  " + line[:160])


def decide_gate():
    bad = 0
    for check in sorted((ROOT / "tools").glob("check-*.py")):
        r = subprocess.run([sys.executable, str(check)], capture_output=True, text=True, cwd=ROOT)
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {check.name}")
        if r.returncode:
            bad += 1
            print("\n".join("     " + l for l in (r.stdout + r.stderr).strip().split("\n")[-6:]))
    sys.exit(1 if bad else 0)


def act_write(path):
    target = inside(path)
    if target.exists():
        target.with_name(target.name + ".bak").write_bytes(target.read_bytes())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sys.stdin.read(), encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)}")


def act_edit(path, old, new):
    target = inside(path)
    text = target.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAILED: OLD occurs {n} times in {path}; it must occur exactly once")
    target.with_name(target.name + ".bak").write_text(text, encoding="utf-8")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"edited {target.relative_to(ROOT)}")


METHODS = {"observe.read": observe_read, "observe.find": observe_find, "observe.search": observe_search,
           "orient.ground": orient_ground, "decide.gate": decide_gate,
           "act.write": act_write, "act.edit": act_edit}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("list", "-h", "--help"):
        print("\n".join(sorted(METHODS)))
        return
    name, args = sys.argv[1], sys.argv[2:]
    if name not in METHODS:
        sys.exit(f"FAILED: unknown method {name}. Known: {', '.join(sorted(METHODS))}")
    try:
        with open(ROOT / ".claude/.matrix-log", "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {name} {' '.join(a[:80] for a in args[:1])}\n")
    except OSError:
        pass
    try:
        METHODS[name](*args)
    except BrokenPipeError:
        sys.exit(0)
    except TypeError:
        sys.exit(f"FAILED: wrong arguments for {name}. See: python3 tools/matrix.py --help")


if __name__ == "__main__":
    main()
