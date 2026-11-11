#!/usr/bin/env python3
"""matrix.py — the Matrix's own tooling: one entry point, called as cardinal.method.

    python3 tools/matrix.py observe.read  PATH [START [END]]
    python3 tools/matrix.py observe.find  GLOB
    python3 tools/matrix.py observe.search PATTERN [PATH]
    python3 tools/matrix.py orient.ground
    python3 tools/matrix.py decide.gate
    python3 tools/matrix.py act.write PATH            (content on stdin; keeps a .bak)
    python3 tools/matrix.py act.edit  PATH OLD NEW    (OLD must occur exactly once)
    python3 tools/matrix.py orient.stall              (open stall incidents, with the stack)
    python3 tools/matrix.py act.resolve ID "CAUSE" "FIX"   (close one; logs to docs/ai-cto/stalls.md)
    python3 tools/matrix.py list

These are the targets the native tools are repointed to (see "repoint" in
.claude/cardinal-map.json). Every call is appended to .claude/.matrix-log.
Paths are confined to the repository. Standard library only.

Hard cap: 10 seconds per call. On a timeout the call exits 124 and writes a
one-time fallback lease (.claude/.matrix-lease/<NativeTool>). The cardinal hook
consumes that lease to let the native tool through exactly once, so a slow
Matrix call never roadblocks the work.

A timeout is also a defect report. It records a stall incident with the stack
at the moment of the stall (.claude/.matrix-stalls/<id>.json). While an incident
is open the cardinal hook says so on every tool call: diagnose why the alias
stalled and improve it before other work, then close it with act.resolve.
"""
import json
import os
import re
import signal
import traceback
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


def orient_stall():
    stalls = sorted((ROOT / ".claude/.matrix-stalls").glob("*.json"))
    if not stalls:
        print("no open stalls")
    for f in stalls:
        d = json.loads(f.read_text())
        print(f"STALL {d['id']} · {d['method']} {' '.join(d['args'])} · cap {d['cap_seconds']}s\n  stalled at:")
        print("".join("    " + line for frame in d["stack"] for line in frame.splitlines(True)))
        print(f"  close with: python3 tools/matrix.py act.resolve {d['id']} \"CAUSE\" \"FIX\"")


def act_resolve(sid, cause, fix):
    f = ROOT / ".claude/.matrix-stalls" / f"{sid}.json"
    if not f.exists():
        sys.exit(f"FAILED: no open stall {sid}")
    d = json.loads(f.read_text())
    log = ROOT / "docs/ai-cto/stalls.md"
    head = ("# Matrix stall log\n\nEvery time a Matrix call breached the 10-second cap: what stalled, why, and what "
            "was improved. Newest first. Written by `tools/matrix.py act.resolve`.\n\n---\n")
    body = log.read_text(encoding="utf-8").split("---\n", 1)[1] if log.exists() else ""
    entry = (f"\n## {sid} · {d['method']}\n\n- **Call:** `{d['method']} {' '.join(d['args'])}` (cap {d['cap_seconds']}s)\n"
             f"- **Cause:** {cause}\n- **Improvement:** {fix}\n")
    log.write_text(head + entry + body, encoding="utf-8")
    f.unlink()
    print(f"resolved {sid}; logged in docs/ai-cto/stalls.md")


METHODS = {"orient.stall": orient_stall, "act.resolve": act_resolve,
           "observe.read": observe_read, "observe.find": observe_find, "observe.search": observe_search,
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
    cap = min(10, int(os.environ.get("MATRIX_TIMEOUT", "10")))  # hard cap: never above 10 s

    def on_timeout(_sig, _frm):
        cfg = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))
        native = [t for t, target in cfg.get("repoint", {}).items() if f"matrix.py {name} " in target + " "]
        lease_dir = ROOT / ".claude/.matrix-lease"
        lease_dir.mkdir(exist_ok=True)
        for t in native:
            (lease_dir / t).write_text(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {name} timed out after {cap}s\n")
        sid = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        stall_dir = ROOT / ".claude/.matrix-stalls"
        stall_dir.mkdir(exist_ok=True)
        (stall_dir / f"{sid}.json").write_text(json.dumps({
            "id": sid, "method": name, "args": [a[:200] for a in args], "cap_seconds": cap,
            "stack": traceback.format_stack(_frm)[-6:]}, indent=2))
        sys.stderr.write(f"FAILED: {name} timed out after {cap}s. One-time fallback lease written for: "
                         f"{', '.join(native) or 'none (no native tool maps to this method)'}\n"
                         f"STALL {sid} recorded. Diagnose and improve the alias now:\n"
                         f"  cd {ROOT} && python3 tools/matrix.py orient.stall\n")
        os._exit(124)

    signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(cap)
    try:
        if os.environ.get("MATRIX_TEST_SLEEP"):  # test hook: simulate a slow call
            time.sleep(float(os.environ["MATRIX_TEST_SLEEP"]))
        METHODS[name](*args)
    except BrokenPipeError:
        sys.exit(0)
    except TypeError:
        sys.exit(f"FAILED: wrong arguments for {name}. See: python3 tools/matrix.py --help")
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
