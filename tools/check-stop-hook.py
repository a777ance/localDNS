#!/usr/bin/env python3
"""check-stop-hook.py — tests the Stop hook (.claude/hooks/decide-act.py) on sample replies.

Each case writes a one-reply transcript in a temp directory, runs the hook on it, and
asserts allow or block (and which rule blocked). It also holds the reply-style rules to
one source: every rule the hook enforces must be named in
.claude/output-styles/briefing.md, so the hook and the style cannot drift apart.

Exit 0 when clean, 1 otherwise.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude/hooks/decide-act.py"
F = "`" * 3  # a code fence, built here so this file never contains one

TILE = ("> **DECISION · DEC-900 · Ship it?**\n> **Action if GO:** ship\n"
        "> **Action if NO GO:** hold\n> **Decision needed:** **GO** or **NO GO**\n")

# (name, reply, the rule key expected to block, or None for allow)
CASES = [
    ("plain done", "**Done.** Pushed abc1234.", None),
    ("state word with colon", "**Blocked**: the gate is red.", None),
    ("no state word", "Pushed abc1234.", "BRIEFING LEAD"),
    ("heading before state word", "## Report\n\n**Done.** Pushed.", "BRIEFING LEAD"),
    ("decide list, nothing acted", "**Waiting.**\n\n**Decide**\n\n1. Run A\n2. Run B\n", "OODA ACT"),
    ("decide list, acted in full", "**Done.**\n\n**Decide**\n\n1. Run A\n2. Run B\n\n**Act**\n\n1. A ran.\n2. B is blocked on DEC-900.\n", None),
    ("decide list, one act line short", "**Partial.**\n\n**Decide**\n\n1. Run A\n2. Run B\n\n**Act**\n\n- A ran.\n", "OODA ACT"),
    ("decide with no list", "**Done.**\n\n**Decide.** Nothing to queue.\n", None),
    ("bash block with cd", f"**Done.** Run:\n\n{F}bash\ncd ~/localDNS\ngit status\n{F}\n", None),
    ("bash block, comment then cd", f"**Done.**\n\n{F}bash\n# check\ncd ~/localDNS && git status\n{F}\n", None),
    ("bash block without cd", f"**Done.** Run:\n\n{F}bash\ngit status\n{F}\n", "COMMAND CD"),
    ("bash block with the cloud container path", f"**Done.**\n\n{F}bash\ncd /home/user/localDNS\ngit status\n{F}\n", "COMMAND CD"),
    ("bash block never rehearsed", f"**Done.** Run:\n\n{F}bash\ncd ~/localDNS\ngit push --force\n{F}\n", "REHEARSE"),
    ("bash block not rehearsed, reason given", f"**Done.**\n\nNot rehearsed: needs a fact from the laptop.\n\n{F}bash\ncd ~/localDNS\nls ../venv\n{F}\n", None),
    ("bash block whose rehearsal failed", f"**Done.**\n\n{F}bash\ncd ~/localDNS\nfalse\n{F}\n", "REHEARSE"),
    ("text block needs no cd", f"**Done.**\n\n{F}text\ngit status\n{F}\n", None),
    ("hedge", "**Done.** The fix should work now.", "NO HEDGE"),
    ("hedge inside a quote is allowed", '**Done.** The style bans "should work" outright.', None),
    ("hedge inside code is allowed", "**Done.** The hook greps for `should work`.", None),
    ("the word probably alone is allowed", "**Done.** The slow call is probably the fetch; `observe.times` confirms it.", None),
    ("complete tile, logged", "**Waiting.**\n\n" + TILE, None),
    ("tile missing a line", "**Waiting.**\n\n" + TILE.replace("> **Action if NO GO:** hold\n", ""), "TILE"),
    ("tile id not in the log", "**Waiting.**\n\n" + TILE.replace("DEC-900", "DEC-901"), "TILE"),
]

# Rule key -> a phrase .claude/output-styles/briefing.md must contain (Q-022: one source).
STYLE = {
    "BRIEFING LEAD": "lead state word",
    "OODA ACT": "Run the queue",
    "COMMAND CD": "starts with `cd ~/localDNS`",
    "NO HEDGE": "vague hedges",
    "TILE": "DECISION · DEC-NNN",
    "REHEARSE": "decide.rehearse",
}


def run(box: Path, reply: str, active=False) -> str:
    transcript = box / "t.jsonl"
    transcript.write_text(json.dumps({"type": "assistant", "message": {
        "role": "assistant", "content": [{"type": "text", "text": reply}]}}) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True, timeout=10,
                       input=json.dumps({"transcript_path": str(transcript), "stop_hook_active": active}),
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(box)})
    return json.loads(r.stdout).get("reason", "") if r.stdout.strip() else ""


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory(prefix="stop-hook-") as tmp:
        box = Path(tmp)
        (box / "docs/ai-cto").mkdir(parents=True)
        (box / "docs/ai-cto/blocked.md").write_text("- **DEC-900 · Ship it? · OPEN**\n", encoding="utf-8")
        import hashlib
        (box / ".claude").mkdir()
        (box / ".claude/.matrix-rehearsed").write_text(
            "".join(f"{hashlib.sha256(c.encode()).hexdigest()}\t{code}\tabc1234\tt\n"
                    for c, code in (("git status", 0), ("false", 1))), encoding="utf-8")
        for name, reply, want in CASES:
            got = run(box, reply)
            if want is None and got:
                fails.append(f"{name}: expected allow, blocked with: {got[:90]}")
            elif want and not got.startswith(want):
                fails.append(f"{name}: expected a {want} block, got: {got[:90] or 'allow'}")
        if run(box, "no state word", active=True):
            fails.append("a second stop in the same turn must be allowed (stop_hook_active)")
        if subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True).stdout.strip():
            fails.append("malformed input must fail open")
    hook_src = HOOK.read_text(encoding="utf-8")
    style = (ROOT / ".claude/output-styles/briefing.md").read_text(encoding="utf-8")
    for key, phrase in STYLE.items():
        if f'"{key}' not in hook_src:
            fails.append(f"rule {key} is listed here but the hook does not enforce it")
        if phrase not in style:
            fails.append(f"the hook enforces {key}, but the output style does not say {phrase!r}")
    tested = {want for _, _, want in CASES if want}
    for key in STYLE:
        if key not in tested:
            fails.append(f"rule {key} has no blocking test case")
    for f in fails:
        print("FAIL", f)
    if not fails:
        print(f"ok   Stop hook: {len(CASES)} replies judged correctly; {len(STYLE)} rules, each named in the output style")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
