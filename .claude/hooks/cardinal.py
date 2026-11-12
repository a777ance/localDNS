#!/usr/bin/env python3
"""PreToolUse hook — names each tool call's cardinal (observe / orient / decide / act).

Reads the hook JSON on stdin, looks the tool up in .claude/cardinal-map.json, and
returns one short line of context such as "cardinal: observe.read". It never blocks:
any error, or an unmapped tool, exits 0 (unmapped tools are reported as such so the
map can be extended). Standard library only.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
READ_ONLY = re.compile(
    r"^\s*(ls|cat|head|tail|grep|rg|find|wc|diff|stat|file|which|command|echo|printf|sort|uniq|cut|tr|test|true|pwd|date|env|"
    r"git\s+(status|log|diff|show|branch|fetch|remote|rev-parse)|python3?\s+tools/check-)\b")


def strip_quoted(cmd: str) -> str:
    """Drop here-document bodies and quoted strings: text a command only quotes is not a call it makes."""
    cmd = re.sub(r"<<-?\s*(['\"]?)(\w+)\1.*?\n\s*\2\b", "<<HEREDOC", cmd, flags=re.DOTALL)
    return re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", cmd)


def classify_bash(cmd: str) -> str:
    cmd = strip_quoted(cmd)
    own = re.search(r"tools/matrix\.py\s+((?:observe|orient|decide|act)\.[\w-]+)", cmd)
    if own:
        return own.group(1)  # a Matrix call names its own cardinal
    if re.search(r"\bgit\s+(commit|push|merge)\b", cmd):
        return "act.ship"
    if re.search(r"tools/check-[\w-]+\.py", cmd) and not re.search(r"\bgit\s+(add|commit)\b|>\s*\S", cmd):
        return "decide.gate"
    # every segment of a compound command must be read-only to count as observe
    parts = [re.sub(r"^\s*(do|then|else)\s+", "", p) for p in re.split(r"&&|\|\||;|\||\n", cmd) if p.strip()]
    parts = [p for p in parts if not re.match(r"^\s*(for|while|if|done|fi)\b", p)]  # shell control words
    if parts and all(READ_ONLY.match(p) or p.strip().startswith("cd ") for p in parts) and ">" not in cmd:
        return "observe.read"
    return "act.write"


def lookup(tool: str, tool_input: dict) -> str:
    if tool == "Bash":
        return classify_bash(str(tool_input.get("command", "")))
    data = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))["cardinals"]
    keys = [tool]
    if tool == "Agent":
        keys.insert(0, f"Agent:{tool_input.get('subagent_type') or 'general-purpose'}")
    if tool == "Skill":
        keys.insert(0, "/" + str(tool_input.get("skill", "")).split(":")[-1])
    if tool == "Read":
        fp = str(tool_input.get("file_path", ""))
        keys.insert(0, "Read:" + fp.split("/localDNS/")[-1])
    for key in keys:
        for cardinal, body in data.items():
            for method, tools in body["methods"].items():
                if key in tools:
                    return f"{cardinal}.{method}"
    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name", "")
        alias = lookup(tool, data.get("tool_input") or {})
        line = f"cardinal: {alias}" if alias else f"cardinal: UNMAPPED ({tool}) — add it to .claude/cardinal-map.json"
        try:  # start stamp for the PostToolUse timing hook (.claude/hooks/timing.py)
            key = re.sub(r"[^\w.-]", "_", str(data.get("tool_use_id") or tool or "unknown"))[:120]
            starts = ROOT / ".claude/.matrix-starts"
            starts.mkdir(exist_ok=True)
            (starts / key).write_text(f"{time.time()}\t{alias or 'UNMAPPED'}", encoding="utf-8")
        except OSError:
            pass
        if data.get("agent_type"):  # set when a subagent made the call
            line += f" · agent: {data['agent_type']}"
        out = {"hookEventName": "PreToolUse", "additionalContext": line}
        cfg = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8"))
        mode = os.environ.get("MATRIX_MODE") or cfg.get("mode", "name")
        target = cfg.get("repoint", {}).get(tool)
        if (ROOT / ".claude/.matrix-off").exists():
            mode = "name"  # kill switch: never warn, never deny
        if target and mode == "warn":
            out["additionalContext"] = f"{line} — Matrix route: {target}"
        lease = ROOT / ".claude/.matrix-lease" / tool
        if target and mode == "enforce" and lease.exists():
            lease.unlink()  # one-time lease: consumed by this call
            out["additionalContext"] = f"{line} — fallback lease consumed: the Matrix call timed out, native {tool} allowed once"
            target = None
        if target and mode == "enforce":
            out["permissionDecision"] = "deny"
            out["permissionDecisionReason"] = (
                f"The Matrix gates native {tool} ({alias}). Use: cd {ROOT} && {target}. "
                "Kill switch: touch .claude/.matrix-off")
        # Probe before egress: a call that changes something outside the session wants a fresh dry run.
        eg = cfg.get("egress", {})
        cmd = strip_quoted(str((data.get("tool_input") or {}).get("command", ""))) if tool == "Bash" else ""
        kind = eg.get("tools", {}).get(tool) or next(
            (k for pat, k in eg.get("bash", {}).items() if re.search(pat, cmd) and "tools/matrix.py" not in cmd), None)
        if kind:
            probe = ROOT / ".claude/.matrix-probes" / kind
            fresh = (probe.exists() and time.time() - probe.stat().st_mtime < eg.get("fresh_seconds", 600)
                     and probe.read_text(encoding="utf-8").startswith("ok"))
            if not fresh:
                out["additionalContext"] += (
                    f" — EGRESS WITHOUT A PROBE: this call changes something outside the session and no "
                    f"passing '{kind}' probe is on record from the last {eg.get('fresh_seconds', 600) // 60} minutes. "
                    f"The probe is lane 0 of 1 + N. Run it first: cd {ROOT} && python3 tools/matrix.py "
                    + {"push": "observe.probe push", "merge": "observe.probe merge BRANCH"}.get(
                        kind, "orient.probe  (or observe.probe / decide.probe / act.probe, whichever fits the goal)"))
        # main is intent cold storage (DEC-015): nothing is pushed to it but the founder's promotions.
        if cmd and re.search(r"\bgit\s+push\b[^|;&\n]*[\s:]main(?![-\w/])", cmd):
            out["additionalContext"] += (
                " — PUSH TO MAIN: main is kept empty on purpose and takes the founder's promotions only. "
                "Work lands on leader, by pull request from your own branch. Do not run this push.")
        # One slow step per call: every 10-second breach of 2026-11-11/12 was a chain of these.
        slow = len(re.findall(r"matrix\.py\s+(?:act\.ship|decide\.rehearse|decide\.gate)\b|\bgit\s+push\b", cmd)) if cmd else 0
        if slow > 1:
            out["additionalContext"] += (
                f" — SLOW CHAIN: this call chains {slow} slow steps (ship, rehearse, gate, push). "
                "Each takes 3 to 6 seconds; together they break the 10-second cap. Run one per call.")
        stalls = sorted((ROOT / ".claude/.matrix-stalls").glob("*.json"))
        if stalls:
            out["additionalContext"] += (
                f" — OPEN MATRIX STALL ({len(stalls)}): a Matrix call breached the 10 s cap. Diagnose why the alias "
                f"stalled and improve it before other work: cd {ROOT} && python3 tools/matrix.py orient.stall")
        print(json.dumps({"hookSpecificOutput": out}))
    except Exception:
        pass  # fail open: naming a call must never stop it
    return 0


if __name__ == "__main__":
    sys.exit(main())
