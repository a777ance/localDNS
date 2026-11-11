#!/usr/bin/env python3
"""check-matrix.py — end-to-end test of the Matrix, run in a throwaway sandbox.

Copies the Matrix (tools/matrix.py, the cardinal hook, the map, the ai-cto registers)
into a temp directory and drives the whole loop there, so the real repo's leases,
stalls, and log are never touched:

  observe  read / find / search / status, and the repo-confinement refusal
  orient   ground / stall
  decide   open, and the hook's cardinal names (including self-naming Matrix calls)
  act      write / edit (with the exactly-once rule)
  gate     name -> warn -> enforce, the kill switch
  cap      timeout -> exit 124 -> one-time lease -> consumed once -> denied again
  stall    incident recorded -> surfaced by the hook -> resolved -> logged

Exit 0 when every step passes, 1 otherwise. Takes about two seconds.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILS = []


def check(name, ok, detail=""):
    if not ok:
        FAILS.append(f"{name}{': ' + detail if detail else ''}")


def main() -> int:
    box = Path(tempfile.mkdtemp(prefix="matrix-e2e-"))
    try:
        for rel in ("tools/matrix.py", ".claude/hooks/cardinal.py", ".claude/cardinal-map.json",
                    "docs/ai-cto/initiatives.md", "docs/ai-cto/debt.md", "docs/ai-cto/blocked.md"):
            (box / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, box / rel)
        (box / "notes.txt").write_text("alpha\nbeta\ngamma\n")
        base_env = {**os.environ, "CLAUDE_PROJECT_DIR": str(box)}
        for k in ("MATRIX_MODE", "MATRIX_TIMEOUT", "MATRIX_TEST_SLEEP"):
            base_env.pop(k, None)

        def mx(*args, stdin=None, **env):
            return subprocess.run([sys.executable, str(box / "tools/matrix.py"), *args], input=stdin,
                                  capture_output=True, text=True, cwd=box, env={**base_env, **env})

        def hook(tool, tool_input=None, mode=None):
            env = {**base_env, **({"MATRIX_MODE": mode} if mode else {})}
            r = subprocess.run([sys.executable, str(box / ".claude/hooks/cardinal.py")],
                               input=json.dumps({"tool_name": tool, "tool_input": tool_input or {}}),
                               capture_output=True, text=True, env=env)
            return json.loads(r.stdout)["hookSpecificOutput"]

        # observe
        r = mx("observe.read", "notes.txt", "2", "2")
        check("observe.read", r.returncode == 0 and "beta" in r.stdout and "alpha" not in r.stdout, r.stderr)
        check("observe.find", "notes.txt" in mx("observe.find", "*.txt").stdout)
        check("observe.search", "notes.txt:3:gamma" in mx("observe.search", "gam+a").stdout)
        check("observe.status", "mode:" in mx("observe.status").stdout)
        check("confinement", mx("observe.read", "/etc/hostname").returncode != 0)
        # orient / decide
        check("orient.ground", "INIT-" in mx("orient.ground").stdout)
        check("orient.stall (none)", "no open stalls" in mx("orient.stall").stdout)
        check("decide.open", mx("decide.open").returncode == 0)
        # act
        check("act.write", mx("act.write", "out.txt", stdin="one two\n").returncode == 0
              and (box / "out.txt").read_text() == "one two\n")
        check("act.edit", mx("act.edit", "out.txt", "two", "three").returncode == 0
              and (box / "out.txt").read_text() == "one three\n")
        (box / "dup.txt").write_text("x x\n")
        check("act.edit exactly-once", mx("act.edit", "dup.txt", "x", "y").returncode != 0)
        check("unknown method", mx("observe.nope").returncode != 0)
        # hook names
        names = {
            ("Read", ""): "observe.read", ("Edit", ""): "act.write", ("AskUserQuestion", ""): "decide.tile",
            ("Bash", "git status --short && ls"): "observe.read",
            ("Bash", "git commit -m x && git push"): "act.ship",
            ("Bash", "rm -rf build"): "act.write",
            ("Bash", "python3 tools/matrix.py orient.ground"): "orient.ground",
        }
        for (tool, cmd), want in names.items():
            got = hook(tool, {"command": cmd} if cmd else {})["additionalContext"]
            check(f"hook names {tool} {cmd}".strip(), got.startswith(f"cardinal: {want}"), got)
        check("hook unmapped", "UNMAPPED" in hook("NoSuchTool")["additionalContext"])
        # gate modes
        check("mode name allows", "permissionDecision" not in hook("Read", mode="name"))
        w = hook("Read", mode="warn")
        check("mode warn allows + routes", "permissionDecision" not in w and "Matrix route" in w["additionalContext"])
        check("mode enforce denies", hook("Read", mode="enforce").get("permissionDecision") == "deny")
        check("enforce leaves Bash alone", "permissionDecision" not in hook("Bash", {"command": "ls"}, mode="enforce"))
        (box / ".claude/.matrix-off").touch()
        check("kill switch", "permissionDecision" not in hook("Read", mode="enforce"))
        (box / ".claude/.matrix-off").unlink()
        # cap -> lease -> stall
        r = mx("observe.read", "notes.txt", MATRIX_TIMEOUT="1", MATRIX_TEST_SLEEP="3")
        check("timeout exits 124", r.returncode == 124, str(r.returncode))
        check("lease written", (box / ".claude/.matrix-lease/Read").exists())
        stalls = list((box / ".claude/.matrix-stalls").glob("*.json"))
        check("stall recorded", len(stalls) == 1)
        check("hook surfaces stall", "OPEN MATRIX STALL" in hook("Glob")["additionalContext"])
        first = hook("Read", mode="enforce")
        check("lease consumed once", "permissionDecision" not in first and "lease consumed" in first["additionalContext"])
        check("then denied again", hook("Read", mode="enforce").get("permissionDecision") == "deny")
        check("orient.stall shows it", stalls and stalls[0].stem in mx("orient.stall").stdout)
        if stalls:
            r = mx("act.resolve", stalls[0].stem, "simulated delay", "none; e2e test")
            check("act.resolve", r.returncode == 0 and (box / "docs/ai-cto/stalls.md").exists(), r.stderr)
        check("stall closed", "OPEN MATRIX STALL" not in hook("Glob")["additionalContext"])
        check("cap cannot be raised", mx("observe.read", "notes.txt", MATRIX_TIMEOUT="99").returncode == 0)
    finally:
        shutil.rmtree(box, ignore_errors=True)
    for f in FAILS:
        print("FAIL", f)
    if not FAILS:
        print("ok   Matrix end to end: observe, orient, decide, act, gate modes, cap, lease, stall")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
