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

        def hook(tool, tool_input=None, mode=None, **extra):
            env = {**base_env, **({"MATRIX_MODE": mode} if mode else {})}
            r = subprocess.run([sys.executable, str(box / ".claude/hooks/cardinal.py")],
                               input=json.dumps({"tool_name": tool, "tool_input": tool_input or {}, **extra}),
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
        check("no .bak beside the file", not list(box.glob("*.bak")) and list((box / ".claude/.matrix-bak").glob("*-out.txt")))
        check("act.undo", mx("act.undo", "out.txt").returncode == 0 and (box / "out.txt").read_text() == "one two\n")
        check("act.undo with no backup fails", mx("act.undo", "notes.txt").returncode != 0)
        tricky = "it's `x` and \"y\"\n$HOME line two\n"
        (box / "old.tmp").write_text("one two\n")
        (box / "new.tmp").write_text(tricky)
        check("act.edit from files", mx("act.edit", "out.txt", "--old-file", "old.tmp", "--new-file", "new.tmp").returncode == 0
              and (box / "out.txt").read_text() == tricky)
        check("act.edit bad arguments", mx("act.edit", "out.txt", "only-one").returncode != 0)
        # bounds (Q-005)
        (box / "long.txt").write_text("".join(f"row {i}\n" for i in range(1, 501)))
        r = mx("observe.read", "long.txt")
        check("observe.read pages at 200", "row 200" in r.stdout and "row 201\n" not in r.stdout and "300 more lines" in r.stdout, r.stdout[-200:])
        check("observe.read explicit range", "row 450" in mx("observe.read", "long.txt", "450", "451").stdout)
        r = mx("observe.search", "^row", "long.txt")
        check("observe.search caps at 200", r.stdout.count("long.txt:") == 200 and "stopped at 200" in r.stdout)
        check("observe.search --max", mx("observe.search", "^row", "long.txt", "--max", "3").stdout.count("long.txt:") == 3)
        (box / "blob.bin").write_bytes(b"gamma\0\1\2")
        (box / "huge.txt").write_text("gamma\n" * 200_000)
        r = mx("observe.search", "gamma")
        check("observe.search skips binary and big files", "blob.bin" not in r.stdout and "huge.txt:" not in r.stdout
              and "2 binary" in r.stdout, r.stdout[-200:])
        check("observe.read refuses binary", mx("observe.read", "blob.bin").returncode != 0)
        check("observe.read refuses a big file with no range", mx("observe.read", "huge.txt").returncode != 0)
        # the Matrix watching itself (Q-009, Q-012, Q-013)
        out = mx("observe.log").stdout
        check("observe.log", "observe.read" in out and "slowest:" in out, out[-200:])
        (box / ".claude/.matrix-log").write_text("".join(f"t\tobserve.read\tx\t0.010\n" for _ in range(2100)))
        mx("observe.status")
        check("log rotates at 2,000 lines", len((box / ".claude/.matrix-log").read_text().split("\n")) < 1100)
        check("observe.times (empty)", "no native tool calls timed" in mx("observe.times").stdout)
        (box / ".claude/.matrix-times").write_text("t1\tRead\tobserve.read\t0.200\nt2\tBash\tact.write\t12.500\nt3\tBash\tobserve.read\t0.400\n")
        out = mx("observe.times").stdout
        check("observe.times", "over 10 s: 1 of 3" in out and "BREACH" in out and "Read" in out, out)
        out = mx("observe.times", "--debt").stdout
        check("observe.times --debt", "DEBT-NNN · Native Bash" in out and "12.5 s" in out and "Read" not in out, out)
        # orient.checkpoint (Q-010)
        (box / "docs/ai-cto/checkpoint.md").write_text("# C\n\n<!-- live:start -->\nold\n<!-- live:end -->\n\nkept\n")
        r1 = mx("orient.checkpoint")
        body = (box / "docs/ai-cto/checkpoint.md").read_text()
        check("orient.checkpoint", "Open decisions" in body and "old" not in body and body.endswith("kept\n"), r1.stdout + r1.stderr)
        check("orient.checkpoint is idempotent", "already current" in mx("orient.checkpoint").stdout)
        check("act.edit exactly-once", mx("act.edit", "dup.txt", "x", "y").returncode != 0)
        check("unknown method", mx("observe.nope").returncode != 0)
        # hook names
        names = {
            ("Read", ""): "observe.read", ("Edit", ""): "act.write", ("AskUserQuestion", ""): "decide.tile",
            ("Bash", "git status --short && ls"): "observe.read",
            ("Bash", "git commit -m x && git push"): "act.ship",
            ("Bash", "rm -rf build"): "act.write",
            ("Bash", "python3 tools/matrix.py orient.ground"): "orient.ground",
            # text a command only quotes is not a call it makes (Q-008)
            ("Bash", "cat <<'EOF'\npython3 tools/matrix.py act.ship x\nEOF"): "observe.read",
            ("Bash", "python3 tools/matrix.py act.write f.txt <<EOF\ngit commit -m x\nEOF"): "act.write",
            ("Bash", "grep -rn 'git commit' docs && echo \"git push\""): "observe.read",
            ("Bash", "python3 - <<'EOF'\nprint('git commit')\nEOF"): "act.write",
            ("Bash", "git commit -m \"it's done\""): "act.ship",
        }
        for (tool, cmd), want in names.items():
            got = hook(tool, {"command": cmd} if cmd else {})["additionalContext"]
            check(f"hook names {tool} {cmd}".strip(), got.startswith(f"cardinal: {want}"), got)
        check("hook names the subagent", hook("Read", agent_type="juror", agent_id="a1")["additionalContext"]
              == "cardinal: observe.read · agent: juror")
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
