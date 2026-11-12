#!/usr/bin/env python3
"""matrix.py — the Matrix's own tooling: one entry point, called as cardinal.method.

    python3 tools/matrix.py observe.read  PATH [START [END]]   (first 200 lines unless a range is given)
    python3 tools/matrix.py observe.find  GLOB
    python3 tools/matrix.py observe.search PATTERN [PATH] [--max N]   (default 200 matches)
    python3 tools/matrix.py observe.probe push             (dry-run the push of this branch; changes nothing)
    python3 tools/matrix.py observe.probe merge BRANCH [BASE]   (would BRANCH merge into BASE cleanly?)
    python3 tools/matrix.py observe.probe path PATH        (size, lines, binary or text, before a read)
    python3 tools/matrix.py observe.probe goal WORDS...   (one probe picks the others from a goal in plain words)
    python3 tools/matrix.py orient.retrofit                (audit what already exists against every enforced rule)
    python3 tools/matrix.py orient.probe                   (is the picture current? checkpoint, decisions, stalls)
    python3 tools/matrix.py decide.probe [FILE...]         (the fast gates only; with a command string: rehearse it)
    python3 tools/matrix.py act.probe ship FILE...         (what would be committed and pushed; changes nothing)
    python3 tools/matrix.py act.probe edit PATH OLD        (would the edit apply exactly once? writes nothing)
    python3 tools/matrix.py observe.log               (Matrix calls per cardinal and method, slowest call)
    python3 tools/matrix.py observe.times [--debt]    (native tool durations; --debt drafts DEBT entries)
    python3 tools/matrix.py orient.checkpoint         (rewrite the live block of docs/ai-cto/checkpoint.md)
    python3 tools/matrix.py observe.status            (branch, changed files, mode, leases, stalls)
    python3 tools/matrix.py orient.ground
    python3 tools/matrix.py decide.gate
    python3 tools/matrix.py decide.open               (founder decisions still OPEN)
    python3 tools/matrix.py decide.rehearse [--at REV] [--setup "CMD"] "COMMAND"
                                                      (run a command meant for the founder in a throwaway
                                                       clone first; pushes go to a throwaway remote)
    python3 tools/matrix.py act.write PATH            (content on stdin; backup in .claude/.matrix-bak)
    python3 tools/matrix.py act.edit  PATH OLD NEW    (OLD must occur exactly once)
    python3 tools/matrix.py act.edit  PATH --old-file F --new-file F   (multi-line text, no shell quoting)
    python3 tools/matrix.py act.undo  PATH            (restore the latest backup of PATH)
    python3 tools/matrix.py act.ship "MESSAGE" FILE... [--push]   (gates first, then commit)
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
SKIP = {".git", "node_modules", "__pycache__", ".matrix-bak"}
BIG = 1_000_000   # observe skips files over 1 MB
PAGE = 200        # default lines for observe.read, default matches for observe.search
CAP = 10          # seconds: the Holy Grail
TRUNK = "leader"  # where work lands. main is intent cold storage and receives nothing (DEC-015).


def inside(p: str) -> Path:
    path = (ROOT / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    if ROOT != path and ROOT not in path.parents:
        sys.exit(f"FAILED: {p} is outside the repository")
    return path


def walk(base=None):
    for d, dirs, files in os.walk(base or ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)  # prune, so .git is never descended
        for f in sorted(files):
            yield Path(d) / f


def is_binary(f: Path) -> bool:
    with open(f, "rb") as fh:
        return b"\0" in fh.read(1024)


def observe_read(path, start=None, end=None):
    f = inside(path)
    if is_binary(f):
        sys.exit(f"FAILED: {path} is a binary file")
    if f.stat().st_size > BIG and not (start and end):
        sys.exit(f"FAILED: {path} is over 1 MB. Give a line range: observe.read {path} START END")
    lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    a = int(start or 1)
    b = int(end) if end else (len(lines) if start else min(len(lines), PAGE))
    for i, line in enumerate(lines[a - 1:b], a):
        print(f"{i:6}\t{line}")
    if b < len(lines) and not end:
        print(f"... {len(lines) - b} more lines. Next: observe.read {path} {b + 1} {min(len(lines), b + PAGE)}")


def observe_find(glob):
    for f in sorted(ROOT.glob(glob)):
        if not (SKIP & set(f.relative_to(ROOT).parts)):
            print(f.relative_to(ROOT))


def observe_search(pattern, *rest):
    rest, limit = list(rest), PAGE
    if "--max" in rest:
        i = rest.index("--max")
        limit = int(rest[i + 1])
        del rest[i:i + 2]
    rx, base = re.compile(pattern), inside(rest[0] if rest else ".")
    hits = skipped = 0
    for f in ([base] if base.is_file() else walk(base)):
        try:
            if f.stat().st_size > BIG or is_binary(f):
                skipped += 1
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
                if rx.search(line):
                    hits += 1
                    if hits > limit:
                        print(f"... stopped at {limit} matches. Narrow the pattern or the path, or raise --max.")
                        return
                    print(f"{f.relative_to(ROOT)}:{i}:{line[:200]}")
        except (UnicodeDecodeError, OSError):
            skipped += 1
    if skipped:
        print(f"({skipped} binary, unreadable, or over-1-MB files skipped)")


def _log_rows():
    f = ROOT / ".claude/.matrix-log"
    for line in (f.read_text(encoding="utf-8").split("\n") if f.exists() else []):
        parts = line.split("\t")
        if len(parts) == 4:  # time, method, first argument, seconds
            yield parts[0], parts[1], parts[2], float(parts[3])


def observe_log():
    rows = list(_log_rows())
    if not rows:
        print("no timed Matrix calls logged yet")
        return
    by = {}
    for _t, method, _a, secs in rows:
        by.setdefault(method, []).append(secs)
    for cardinal in ("observe", "orient", "decide", "act"):
        mine = {m: s for m, s in by.items() if m.startswith(cardinal + ".")}
        print(f"{cardinal:8} {sum(len(s) for s in mine.values()):5} calls")
        for m in sorted(mine, key=lambda m: -len(mine[m])):
            print(f"  {m:20} {len(mine[m]):5}   worst {max(mine[m]):5.2f}s")
    when, method, arg, secs = max(rows, key=lambda r: r[3])
    print(f"slowest: {method} {arg} · {secs:.2f}s · {when}")


def _times_rows():
    f = ROOT / ".claude/.matrix-times"
    for line in (f.read_text(encoding="utf-8").split("\n") if f.exists() else []):
        parts = line.split("\t")
        if len(parts) == 4:  # time, tool, cardinal, seconds
            yield parts[0], parts[1], parts[2], float(parts[3])


def observe_times(*flags):
    rows = list(_times_rows())
    if not rows:
        print("no native tool calls timed yet (.claude/.matrix-times is empty)")
        return
    if "--debt" in flags:
        worst = {}
        for when, tool, cardinal, secs in rows:
            if secs > CAP and secs > worst.get(tool, ("", "", 0))[2]:
                worst[tool] = (when, cardinal, secs)
        for tool in sorted(worst, reverse=True):
            when, cardinal, secs = worst[tool]
            n = sum(1 for r in rows if r[1] == tool and r[3] > CAP)
            print(f"## DEBT-NNN · Native {tool} broke the 10-second cap · Open\n\n"
                  f"- **Measured:** worst call {secs:.1f} s ({cardinal}, {when}); {n} of "
                  f"{sum(1 for r in rows if r[1] == tool)} timed calls over 10 s. Source: `.claude/.matrix-times`.\n"
                  f"- **Fix:** find what the slow calls had in common, then bound or split the call.\n")
        if not worst:
            print("no tool broke the 10-second cap; no debt to record")
        return
    med = lambda s: sorted(s)[len(s) // 2]
    for label, col in (("tool", 1), ("cardinal", 2)):
        groups = {}
        for r in rows:
            groups.setdefault(r[col], []).append(r[3])
        print(f"{label:28} count  median   worst")
        for k in sorted(groups, key=lambda k: -max(groups[k])):
            print(f"  {k[:26]:26} {len(groups[k]):5} {med(groups[k]):6.2f}s {max(groups[k]):6.2f}s")
    over = [r for r in rows if r[3] > CAP]
    print(f"over 10 s: {len(over)} of {len(rows)} calls")
    for when, tool, cardinal, secs in over:
        print(f"  BREACH {secs:6.1f}s  {tool} ({cardinal})  {when}")


def orient_ground():
    for name in ("initiatives.md", "debt.md", "blocked.md"):
        print(f"== docs/ai-cto/{name}")
        for line in (ROOT / "docs/ai-cto" / name).read_text(encoding="utf-8").split("\n"):
            if line.startswith("## ") or line.startswith("- **DEC-"):
                print("  " + line[:160])


def decide_gate():
    bad = 0
    for check in sorted((ROOT / "tools").glob("check-*.py")):
        t0 = time.time()
        r = subprocess.run([sys.executable, str(check)], capture_output=True, text=True, cwd=ROOT)
        took = time.time() - t0
        slow = "  SLOW: over the 10 s Holy Grail" if took > 10 else ""
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {check.name:26} {took:5.1f}s{slow}")
        if r.returncode:
            bad += 1
            print("\n".join("     " + l for l in (r.stdout + r.stderr).strip().split("\n")[-6:]))
    sys.exit(1 if bad else 0)


def _backup(target: Path):
    bak = ROOT / ".claude/.matrix-bak"
    bak.mkdir(parents=True, exist_ok=True)
    name = str(target.relative_to(ROOT)).replace("/", "__")
    (bak / f"{time.time_ns()}-{name}").write_bytes(target.read_bytes())


def act_write(path):
    target = inside(path)
    if target.exists():
        _backup(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sys.stdin.read(), encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)}")


def act_edit(path, *rest):
    target, rest = inside(path), list(rest)
    if "--old-file" in rest and "--new-file" in rest:  # multi-line text without shell quoting
        old = Path(rest[rest.index("--old-file") + 1]).read_text(encoding="utf-8")
        new = Path(rest[rest.index("--new-file") + 1]).read_text(encoding="utf-8")
    elif len(rest) == 2:
        old, new = rest
    else:
        sys.exit("FAILED: act.edit takes PATH OLD NEW, or PATH --old-file F --new-file F")
    text = target.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAILED: OLD occurs {n} times in {path}; it must occur exactly once")
    _backup(target)
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"edited {target.relative_to(ROOT)}")


def act_undo(path):
    target = inside(path)
    name = str(target.relative_to(ROOT)).replace("/", "__")
    baks = sorted(f for f in (ROOT / ".claude/.matrix-bak").glob("*-" + name) if f.name.split("-", 1)[1] == name)
    if not baks:
        sys.exit(f"FAILED: no backup of {path}")
    target.write_bytes(baks[-1].read_bytes())
    baks[-1].unlink()  # consumed, so a second undo steps one edit further back
    print(f"restored {target.relative_to(ROOT)} ({len(baks) - 1} older backups left)")


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


def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT)


AGENT_LEDGER = ROOT / ".claude/.agent-ledger"


def observe_agents(kind="status", *args):
    """The agent ledger: a launch is recorded by the Matrix hook (every Agent call); a finish is recorded
    with `observe.agents finish ID`, because a completion notice does not reach a hook.

    `observe.agents status` prints the running count. `observe.agents check` exits 1 while any agent is
    running, so the repo's check-all fails closed until every launch has a finish.
    """
    lines = AGENT_LEDGER.read_text(encoding="utf-8").splitlines() if AGENT_LEDGER.exists() else []
    if kind == "launch":
        AGENT_LEDGER.parent.mkdir(exist_ok=True)
        with AGENT_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(f"launch\t{args[0] if args else '?'}\n")
        return 0
    if kind == "finish":
        if not args:
            sys.exit("FAILED: observe.agents finish takes the agent id")
        AGENT_LEDGER.parent.mkdir(exist_ok=True)
        with AGENT_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(f"finish\t{args[0]}\n")
        return 0
    launched = [ln.split("\t", 1)[1] for ln in lines if ln.startswith("launch\t")]
    finished = {ln.split("\t", 1)[1] for ln in lines if ln.startswith("finish\t")}
    running = [i for i in launched if i not in finished]
    print(f"agents running: {len(running)} · launched {len(launched)} · finished {len(finished)}")
    if kind == "check" and running:
        sys.exit(1)  # the dispatcher ignores return values; the exit code is what check-all reads
    return 0


def observe_status():
    cfg = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))
    off = (ROOT / ".claude/.matrix-off").exists()
    print(f"branch:  {_git('branch', '--show-current').stdout.strip() or '(none)'}")
    print(f"mode:    {cfg.get('mode')}{' (kill switch ON: forced to name)' if off else ''}")
    changed = _git("status", "--short").stdout.strip()
    print("changed: " + (changed.replace(chr(10), chr(10) + "         ") if changed else "nothing"))
    leases = sorted(f.name for f in (ROOT / ".claude/.matrix-lease").glob("*"))
    stalls = sorted(f.stem for f in (ROOT / ".claude/.matrix-stalls").glob("*.json"))
    print(f"leases:  {', '.join(leases) or 'none'}")
    print(f"stalls:  {', '.join(stalls) or 'none'}")


def decide_open():
    text = (ROOT / "docs/ai-cto/blocked.md").read_text(encoding="utf-8")
    rows = re.findall(r"^- \*\*(DEC-\d{3}) · (.*?) · OPEN\*\*", text, re.MULTILINE)
    for dec, question in rows:
        print(f"{dec} · {question}")
    if not rows:
        print("no open decisions")


def orient_checkpoint():
    f = ROOT / "docs/ai-cto/checkpoint.md"
    text = f.read_text(encoding="utf-8")
    start, stop = "<!-- live:start -->", "<!-- live:end -->"
    if start not in text or stop not in text:
        sys.exit(f"FAILED: docs/ai-cto/checkpoint.md has no {start} ... {stop} block")
    handoff = ROOT / "docs/ai-cto/handoff.md"
    lease = re.search(r"`(start: [^`]*expiry: [^`]*)`", handoff.read_text(encoding="utf-8") if handoff.exists() else "")
    opens = re.findall(r"^- \*\*(DEC-\d{3}) · (.*?) · OPEN\*\*",
                       (ROOT / "docs/ai-cto/blocked.md").read_text(encoding="utf-8"), re.MULTILINE)
    stalls = sorted(s.stem for s in (ROOT / ".claude/.matrix-stalls").glob("*.json"))
    commits = _git("log", "--format=%h %s", "-5").stdout.strip().split("\n")
    body = [f"- **Branch:** `{_git('branch', '--show-current').stdout.strip() or '(none)'}`",
            f"- **Lease:** {lease.group(1) if lease else 'none recorded'}",
            f"- **Open decisions:** {', '.join(d for d, _ in opens) or 'none'}",
            f"- **Open stalls:** {', '.join(stalls) or 'none'}",
            "- **Last five commits:**"] + [f"  - {c.replace('`', chr(39))}" for c in commits if c]
    head, tail = text.split(start, 1)[0], text.split(stop, 1)[1]
    new = head + start + "\n" + "\n".join(body) + "\n" + stop + tail
    if new == text:
        print("checkpoint already current")
        return
    f.write_text(new, encoding="utf-8")
    print("rewrote the live block of docs/ai-cto/checkpoint.md")


def _record_probe(kind, target, ok, note):
    d = ROOT / ".claude/.matrix-probes"
    d.mkdir(exist_ok=True)
    line = f"{'ok' if ok else 'FAILED'}\t{target}\t{note}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
    (d / kind).write_text(line, encoding="utf-8")
    (d / "any").write_text(line, encoding="utf-8")  # lane 0 ran: any probe counts before lanes are opened


def probe_push():
    """Dry-run the push of the current branch. Returns (ok, note). Changes nothing on the remote."""
    branch = _git("branch", "--show-current").stdout.strip()
    if not branch:
        return False, "not on a branch"
    r = _git("push", "--dry-run", "--porcelain", "origin", branch)
    last = (r.stdout + r.stderr).strip().split("\n")
    note = next((l.strip() for l in last if l.startswith(("=", "*", " ", "!", "+", "-"))), last[-1] if last else "")
    _record_probe("push", branch, r.returncode == 0, note[:120])
    return r.returncode == 0, f"{branch}: {note[:160]}"


def probe_goal(words):
    """SQ-009: one probe that picks the others from a goal in plain words. It names the probes it
    chose and why, then runs them. Egress goals run the egress probes; anything else gets the
    orient probe, which changes nothing and fits every other goal."""
    text = " ".join(words).lower()
    picks = []
    if re.search(r"\b(push|ship|publish|deploy|send|upload)\b", text):
        picks.append(("push", "the goal sends work outside the session"))
    if re.search(r"\b(merge|pull request|\bpr\b|land)\b", text):
        picks.append(("merge", "the goal merges a branch into leader"))
    if not picks:
        print(f"probe goal: no outward step named in {text!r}; the orient probe fits")
        return observe_probe("orient-fallback")
    for kind, why in picks:
        print(f"probe goal picks {kind}: {why}")
        if kind == "push":
            observe_probe("push")
        else:
            branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
                                    text=True, cwd=ROOT).stdout.strip()
            observe_probe("merge", branch, "leader")


def observe_probe(kind="", *args):
    """Dry-run an action that reaches outside the session, before doing it."""
    if kind == "goal":
        return probe_goal(args)
    if kind == "orient-fallback":
        return orient_probe()
    if kind == "push":
        ok, note = probe_push()
        print(f"probe push {'ok' if ok else 'FAILED'} · {note}")
    elif kind == "merge" and args:
        branch, base = args[0], (args[1] if len(args) > 1 else TRUNK)
        _git("fetch", "-q", "origin", branch, base)
        tip, onto = (_git("rev-parse", "--verify", f"origin/{x}^{{commit}}").stdout.strip() for x in (branch, base))
        if not tip or not onto:
            sys.exit(f"FAILED: origin/{branch} or origin/{base} is not known here")
        ahead = _git("rev-list", "--count", f"{onto}..{tip}").stdout.strip()
        behind = _git("rev-list", "--count", f"{tip}..{onto}").stdout.strip()
        clean = _git("merge-tree", "--write-tree", onto, tip).returncode == 0
        ok = clean and ahead != "0"
        note = f"{ahead} ahead, {behind} behind, {'no conflicts' if clean else 'CONFLICTS'}, head {tip}"
        _record_probe("merge", branch, ok, note)
        print(f"probe merge {'ok' if ok else 'FAILED'} · origin/{branch} into origin/{base} · {note}")
        files = _git("diff", "--stat", f"{onto}...{tip}").stdout.strip().split("\n")
        print("\n".join("  " + l for l in files[-6:]))
    elif kind == "path" and args:
        f = inside(args[0])
        ok = f.is_file()
        if ok:
            size, binary = f.stat().st_size, is_binary(f)
            lines = 0 if binary or size > BIG else f.read_text(encoding="utf-8", errors="replace").count("\n")
            note = f"{size} bytes, " + ("binary" if binary else "over 1 MB: give a range" if size > BIG else
                                        f"{lines} lines" + (f": read in pages of {PAGE}" if lines > PAGE else ""))
        else:
            note = "a directory: use observe.find" if f.is_dir() else "does not exist"
        _record_probe("path", args[0], ok, note)
        print(f"probe path {'ok' if ok else 'FAILED'} · {args[0]} · {note}")
    else:
        sys.exit("FAILED: observe.probe takes: push  |  merge BRANCH [BASE]  |  path PATH")
    if not ok:
        sys.exit(1)


FAST_GATES = ("check-cardinal.py", "check-decisions.py", "check-docs.py", "check-doctrine.py",
              "check-provenance.py", "check-registers.py")  # each under a second; the end-to-end tests are not here


def _fast_gates():
    bad = []
    for name in FAST_GATES:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / name)], capture_output=True, text=True, cwd=ROOT)
        if r.returncode:
            bad.append(f"{name}: {(r.stdout + r.stderr).strip().splitlines()[-1][:140]}")
    return bad


def orient_probe():
    """Lane 0 for Orient: is the picture this session is about to reason from still current?"""
    notes = []
    cp = ROOT / "docs/ai-cto/checkpoint.md"
    head = _git("log", "--format=%h", "-1").stdout.strip()
    # The checkpoint cannot name the commit that contains it, so "current" means: touched in the last five commits.
    if cp.exists() and head and not _git("log", "-5", "--format=%h", "--", "docs/ai-cto/checkpoint.md").stdout.strip():
        notes.append("checkpoint has not been touched in the last five commits: run orient.checkpoint")
    dirty = _git("status", "--short").stdout.strip()
    if dirty:
        notes.append(f"{len(dirty.splitlines())} uncommitted file(s)")
    stalls = list((ROOT / ".claude/.matrix-stalls").glob("*.json"))
    if stalls:
        notes.append(f"{len(stalls)} open stall(s): run orient.stall first")
    opens = re.findall(r"^- \*\*(DEC-\d{3}) · .*? · OPEN\*\*", (ROOT / "docs/ai-cto/blocked.md").read_text(encoding="utf-8"), re.MULTILINE)
    ok = not stalls
    _record_probe("orient", head, ok, "; ".join(notes)[:120])
    print(f"probe orient {'ok' if ok else 'FAILED'} · commit {head} · open decisions: {', '.join(opens) or 'none'}")
    for n in notes:
        print("  note: " + n)
    if not ok:
        sys.exit(1)


def decide_probe(*args):
    """Lane 0 for Decide: the fast gates only. A single argument with a space in it is a command: rehearse it."""
    if len(args) == 1 and " " in args[0]:
        return decide_rehearse(args[0])
    bad = _fast_gates()
    _record_probe("decide", "fast gates", not bad, "; ".join(bad)[:120])
    print(f"probe decide {'ok' if not bad else 'FAILED'} · {len(FAST_GATES) - len(bad)} of {len(FAST_GATES)} fast gates pass"
          " (the end-to-end tests run in decide.gate)")
    for b in bad:
        print("  FAIL " + b)
    if bad:
        sys.exit(1)


def act_probe(kind="", *args):
    """Lane 0 for Act: say what the action would do, and whether it would work, without doing it."""
    if kind == "edit" and len(args) == 2:
        n = inside(args[0]).read_text(encoding="utf-8").count(args[1])
        ok, target, note = n == 1, args[0], f"OLD occurs {n} time(s); an edit needs exactly 1"
    elif kind == "ship" and args:
        for f in args:
            inside(f)
        changed = _git("status", "--short", "--", *args).stdout.strip().splitlines()
        bad = _fast_gates()
        pushed, pnote = probe_push()
        ok = bool(changed) and not bad and pushed
        target = " ".join(args)[:60]
        note = (f"{len(changed)} file(s) would be committed; fast gates {'pass' if not bad else 'FAIL: ' + bad[0]}; "
                f"push dry run {'ok' if pushed else 'FAILED: ' + pnote}")
        if not changed:
            note = "nothing to commit in those paths; " + note
    else:
        sys.exit("FAILED: act.probe takes: ship FILE...  |  edit PATH OLD")
    _record_probe("act", target, ok, note[:120])
    print(f"probe act {kind} {'ok' if ok else 'FAILED'} · {note}")
    if not ok:
        sys.exit(1)


# ---- Retrofit (retro-compliance, INIT-007): a new rule reaches backward. Every rule the Stop hook
# enforces on replies has an entry here: an audit over what already exists, or the reason there is
# nothing stored to audit. tools/check-stop-hook.py fails if a rule has no entry.
FOUNDER_DOCS = ("CLAUDE.md", "README.md", "docs/ai-cto", ".claude/output-styles")
RETROFIT_EXEMPT = {"docs/ai-cto/handoff.md": "written for a cloud session, where the container path is the right one",
                   "docs/ai-cto/handoff-2026-11-11.md": "the archived first handoff, also written for a cloud session",
                   "docs/ai-cto/reply-style-full.md": "the archived long form of the rules; it quotes what they forbid"}
HEDGES = ("should work", "probably works", "probably work", "may have worked", "might have worked", "should be fine")


def _founder_docs():
    for entry in FOUNDER_DOCS:
        base = ROOT / entry
        for f in ([base] if base.is_file() else sorted(base.rglob("*.md")) if base.is_dir() else []):
            rel = str(f.relative_to(ROOT))
            if rel not in RETROFIT_EXEMPT:
                yield rel, f.read_text(encoding="utf-8", errors="replace")


def _bash_blocks(text):
    return re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL)


def audit_cd():
    return [f"{rel}: a bash block uses the cloud container path /home/user/" for rel, text in _founder_docs()
            if any(re.search(r"^\s*cd /home/user/", b, re.MULTILINE) for b in _bash_blocks(text))]


def audit_hedge():
    out = []
    for rel, text in _founder_docs():
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        prose = re.sub(r"[\"\u201c][^\"\u201d\n]*[\"\u201d]", "", prose).lower()
        out += [f"{rel}: says {h!r} outside a quote" for h in HEDGES if h in prose]
    return out


def audit_rehearse():
    import hashlib
    f = ROOT / ".claude/.matrix-rehearsed"
    done = {l.split("\t")[0] for l in (f.read_text(encoding="utf-8").splitlines() if f.exists() else [])
            if l.split("\t")[1:2] == ["0"]}
    out = []
    for rel in ("docs/ai-cto/roadmap.md",):  # the docs that hand the founder commands to paste
        text = (ROOT / rel).read_text(encoding="utf-8") if (ROOT / rel).exists() else ""
        if "Not rehearsed:" in text:
            continue
        out += [f"{rel}: command never rehearsed here: {norm_command(b)[:70]!r}" for b in _bash_blocks(text)
                if norm_command(b) and hashlib.sha256(norm_command(b).encode()).hexdigest() not in done]
    return out


def audit_scratch():
    import glob
    f = ROOT / ".claude/.matrix-scratch"
    known = set(f.read_text(encoding="utf-8").splitlines()) if f.exists() else set()
    return [f"unannounced scratchpad entry: {e}" for e in sorted(glob.glob("/tmp/claude-*/*/*/scratchpad/*")) if e not in known]


RETROFIT = {
    "BRIEFING LEAD": "applies to a reply as it is sent; no replies are stored to audit",
    "OODA ACT": "applies to a reply as it is sent; no replies are stored to audit",
    "COMMAND CD": audit_cd,
    "REHEARSE": audit_rehearse,
    "NO HEDGE": audit_hedge,
    "TILE": "stored decisions are audited on every commit by tools/check-decisions.py",
    "SCRATCHPAD": audit_scratch,
    "LANDING": "applies to a reply as it is sent; no replies are stored to audit",
    "L ITEMS OPEN": "applies at the moment a turn ends; open items live in the reply, and the queue is audited by NEXT ACTION",
    "L STEP": "applies to a reply as it is sent; no replies are stored to audit",
    "NEXT ACTION": "applies at the moment a turn ends; it reads the live queue, so there is no past state to audit",
}


def orient_retrofit():
    """Apply every enforced rule to what already exists, and list what does not comply."""
    total = 0
    for rule, audit in RETROFIT.items():
        if isinstance(audit, str):
            print(f"n/a  {rule:14} {audit}")
            continue
        found = audit()
        total += len(found)
        print(f"{'ok  ' if not found else 'FIX '} {rule:14} {len(found)} finding(s)")
        for line in found[:10]:
            print("       " + line)
    for rel, why in RETROFIT_EXEMPT.items():
        print(f"exempt {rel}: {why}")
    print("gates: the nine checks in decide.gate audit all stored state on every commit")
    if total:
        sys.exit(f"FAILED: {total} retrofit finding(s). Fix each, or exempt it in RETROFIT_EXEMPT with the reason.")


def norm_command(text: str) -> str:
    """A command as the Stop hook compares it: no blank lines, comments, or leading cd to the repo."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
    if lines and re.match(r"cd\s+\S+$", lines[0]):
        lines = lines[1:]
    elif lines:  # the one-line form: cd REPO && command
        lines[0] = re.sub(r"^cd\s+\S+\s*&&\s*", "", lines[0])
    return "\n".join(lines)


def decide_rehearse(*rest):
    """Look before the founder leaps: run his command here first, in the state his checkout is in."""
    import hashlib
    import shutil
    import tempfile
    rest, at, setup = list(rest), f"origin/{TRUNK}", ""
    for flag in ("--at", "--setup"):
        if flag in rest:
            i = rest.index(flag)
            if flag == "--at":
                at = rest[i + 1]
            else:
                setup = rest[i + 1]
            del rest[i:i + 2]
    if len(rest) != 1:
        sys.exit('FAILED: decide.rehearse takes one COMMAND string (plus optional --at REV, --setup "CMD")')
    command = norm_command(rest[0])
    rev = _git("rev-parse", "--verify", at + "^{commit}").stdout.strip()
    tip = _git("rev-parse", "--verify", f"origin/{TRUNK}^{{commit}}").stdout.strip() or rev
    if not rev:
        sys.exit(f"FAILED: {at} is not a commit here. Fetch first.")
    box = Path(tempfile.mkdtemp(prefix="rehearse-"))
    try:
        def run(*cmd, cwd=None, **kw):
            return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)
        work = box / "localDNS"
        # --mirror, not --bare: the remote's main is usually known here only as origin/main, and a
        # bare clone copies local branches alone, so its "main" would be a stale one (found 2026-11-11).
        steps = [(("git", "clone", "-q", "--mirror", str(ROOT), str(box / "remote.git")), None),
                 (("git", "--git-dir", str(box / "remote.git"), "update-ref", f"refs/heads/{TRUNK}", tip), None),
                 (("git", "clone", "-q", "-b", TRUNK, str(box / "remote.git"), str(work)), None),
                 (("git", "reset", "-q", "--hard", rev), work)]
        for cmd, cwd in steps:
            s = run(*cmd, cwd=cwd)
            if s.returncode:
                sys.exit(f"FAILED: could not build the rehearsal copy ({' '.join(cmd[:3])}): {s.stderr.strip()[-200:]}")
        seen = run("git", "rev-parse", f"origin/{TRUNK}", cwd=work).stdout.strip()
        if seen != tip:
            sys.exit(f"FAILED: the rehearsal copy's origin/{TRUNK} is {seen[:7]}, not {tip[:7]}; refusing to rehearse a wrong state")
        env = {**os.environ, "HOME": str(box), "GIT_AUTHOR_NAME": "rehearsal", "GIT_AUTHOR_EMAIL": "rehearsal@localhost",
               "GIT_COMMITTER_NAME": "rehearsal", "GIT_COMMITTER_EMAIL": "rehearsal@localhost"}
        if setup:
            s = run("bash", "-c", setup, cwd=work, env=env, timeout=60)
            if s.returncode:
                sys.exit(f"FAILED: the --setup command exited {s.returncode}: {(s.stdout + s.stderr)[-300:]}")
        try:
            r = run("bash", "-c", command, cwd=work, env=env, timeout=90)
            code, out = r.returncode, (r.stdout + r.stderr).strip()
        except subprocess.TimeoutExpired:
            code, out = 124, "timed out after 90 s"
        print(f"rehearsed at {rev[:7]} (remote {TRUNK} at {tip[:7]}){' after setup' if setup else ''}: exit {code}")
        print("\n".join("  " + l for l in out.split("\n")[-12:]))
        digest = hashlib.sha256(command.encode()).hexdigest()
        with open(ROOT / ".claude/.matrix-rehearsed", "a", encoding="utf-8") as fh:
            fh.write(f"{digest}\t{code}\t{rev[:7]}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        if code:
            sys.exit(f"FAILED: do not hand this command to the founder. It exits {code} in a copy of his checkout.")
    finally:
        shutil.rmtree(box, ignore_errors=True)


def act_ship(message, *rest):
    push = "--push" in rest
    files = [f for f in rest if f != "--push"]
    if not files:
        sys.exit("FAILED: name the files to ship. Nothing is staged implicitly.")
    # The gates run side by side: in sequence they took the ship past the 10-second cap (seen 2026-11-12).
    from concurrent.futures import ThreadPoolExecutor
    checks = sorted((ROOT / "tools").glob("check-*.py"))
    with ThreadPoolExecutor(max_workers=len(checks) or 1) as pool:
        results = list(pool.map(lambda c: subprocess.run([sys.executable, str(c)], capture_output=True, text=True, cwd=ROOT), checks))
    for check, r in zip(checks, results):
        if r.returncode:
            sys.exit(f"FAILED: gate {check.name} is red; nothing committed.\n" + (r.stdout + r.stderr)[-600:])
    for f in files:
        inside(f)
    if push:  # probe before egress: a push that cannot land is found before anything is committed
        ok, note = probe_push()
        if not ok:
            sys.exit(f"FAILED: push probe (dry run) failed; nothing committed. {note}")
    r = _git("add", "--", *files)
    if r.returncode:
        sys.exit("FAILED: git add: " + r.stderr.strip())
    r = _git("commit", "-q", "-m", message)
    if r.returncode:
        sys.exit("FAILED: git commit: " + (r.stdout + r.stderr).strip())
    print("committed " + _git("log", "--oneline", "-1").stdout.strip())
    if push:
        branch = _git("branch", "--show-current").stdout.strip()
        for wait in (0, 2, 4, 8, 16):
            time.sleep(wait)
            r = _git("push", "-u", "origin", branch)
            if r.returncode == 0:
                print(f"pushed to origin/{branch}")
                return
        sys.exit("FAILED: git push after 5 tries: " + r.stderr.strip()[-300:])


def observe_hitrate():
    """SQ-hitrate: the share of file-touching Bash calls routed through the Matrix this session.

    Routed = a tools/matrix.py call. Raw = a plain file verb (cat, grep, sed, ...). The hook writes one
    line per call to .claude/.matrix-hitrate; this prints the totals and the rate.
    """
    log = ROOT / ".claude/.matrix-hitrate"
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    routed = sum(1 for ln in lines if ln.startswith("routed"))
    raw = sum(1 for ln in lines if ln.startswith("raw"))
    total = routed + raw
    rate = (100.0 * routed / total) if total else 0.0
    verbs = {}
    for ln in lines:
        if ln.startswith("raw"):
            verb = ln.split("\t", 1)[1] if "\t" in ln else "?"
            verbs[verb] = verbs.get(verb, 0) + 1
    print(f"hit rate {rate:.1f}% · routed {routed} · raw {raw} · file-touching calls {total}")
    for verb, n in sorted(verbs.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  raw {verb}: {n}")
    return 0


METHODS = {"observe.hitrate": observe_hitrate, "observe.agents": observe_agents,"observe.status": observe_status,"decide.open": decide_open, "act.ship": act_ship,
           "orient.stall": orient_stall, "act.resolve": act_resolve,
           "observe.read": observe_read, "observe.find": observe_find, "observe.search": observe_search,
           "orient.ground": orient_ground, "decide.gate": decide_gate,
           "act.write": act_write, "act.edit": act_edit, "act.undo": act_undo,
           "observe.log": observe_log, "observe.times": observe_times, "orient.checkpoint": orient_checkpoint,
           "decide.rehearse": decide_rehearse, "observe.probe": observe_probe,
           "orient.probe": orient_probe, "orient.retrofit": orient_retrofit, "decide.probe": decide_probe, "act.probe": act_probe}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("list", "-h", "--help"):
        print("\n".join(sorted(METHODS)))
        return
    name, args = sys.argv[1], sys.argv[2:]
    if name not in METHODS:
        sys.exit(f"FAILED: unknown method {name}. Known: {', '.join(sorted(METHODS))}")
    t0 = time.time()

    def log_call():
        try:
            f = ROOT / ".claude/.matrix-log"
            arg = (args[0] if args else "")[:80].replace("\t", " ").replace("\n", " ")
            with open(f, "a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\t{name}\t{arg}\t{time.time() - t0:.3f}\n")
            lines = f.read_text(encoding="utf-8").split("\n")
            if len(lines) > 2000:  # rotate: keep the newest 1,000 calls
                f.write_text("\n".join(lines[-1001:]), encoding="utf-8")
        except OSError:
            pass

    cap = min(CAP, int(os.environ.get("MATRIX_TIMEOUT", str(CAP))))  # hard cap: never above 10 s

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
        log_call()
        os._exit(124)

    signal.signal(signal.SIGALRM, on_timeout)
    if name not in ("act.ship", "decide.gate", "decide.rehearse", "decide.probe", "act.probe"):  # these run several steps; each step is timed instead
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
        log_call()


if __name__ == "__main__":
    main()
