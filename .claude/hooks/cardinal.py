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

# Hard guards: destructive shell and state polling are denied in every mode (see main()).
HARD_BASH = re.compile(r"\brm\s+-[a-zA-Z]*[rRf]|\brm\s+--(recursive|force)|\bgit\s+push\b.*--force(?!-with-lease)|"
                       r"\bgit\s+push\b.*\s-f\b|\bgit\s+reset\s+--hard\b|\bgit\s+clean\b.*-[a-zA-Z]*f|"
                       r"\bmkfs(\.|\s)|\bdd\s+if=|\bshutdown\b|\breboot\b|\bdocker\s+(system\s+prune|rm\s+-f)")
HARD_POLL_TOOLS = {"ReadNotifications", "mcp__github__pull_request_read", "mcp__github__get_check_run",
                   "mcp__github__actions_get", "mcp__github__actions_list",
                   "mcp__claude-code-remote__list_events", "mcp__claude-code-remote__get_event"}
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
        # Hard guards (the safety goals of the alias routers, kept in the Matrix). They deny in EVERY
        # mode, because they are bans, not routes. The break-glass is the documented kill switch.
        if not (ROOT / ".claude/.matrix-off").exists():
            poll = tool in HARD_POLL_TOOLS
            cmd_ = str((data.get("tool_input") or {}).get("command", "")) if tool == "Bash" else ""
            destructive = bool(cmd_) and bool(HARD_BASH.search(cmd_))
            if poll or destructive:
                why = (f"{tool} polls PR, CI or notification state. PR and CI events arrive on their own; polling is banned."
                       if poll else
                       "Destructive shell command banned in every mode (hard guard). Use a non-destructive form, or ask the user to run it.")
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                         "permissionDecision": "deny",
                                                         "permissionDecisionReason": why}}))
                return 0
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
        # The letter of the active cardinal leads each step (founder's rule, 2026-11-12): O, OO, D, A.
        if tool == "Bash" and alias:
            want = {"observe": "O", "orient": "OO", "decide": "D", "act": "A"}.get(alias.split(".")[0])
            said = str((data.get("tool_input") or {}).get("description", ""))
            if want and not re.match(r"^%s · \S" % want, said):
                out["additionalContext"] += (
                    f" — LETTER: this call is {alias}; its description must start with '{want} · ' "
                    "(O observe, OO orient, D decide, A act). One command, one letter.")
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
        # SQ-007: three or more act calls in a row with no observe or orient between them. The
        # trail is the last 20 cardinals; a run of act at its end is what this names.
        try:
            trail_path = ROOT / ".claude/.matrix-recent"
            trail = json.loads(trail_path.read_text(encoding="utf-8")) if trail_path.exists() else []
            trail = (trail + [alias.split(".")[0] if alias else "unmapped"])[-20:]
            trail_path.write_text(json.dumps(trail), encoding="utf-8")
            run = 0
            for c in reversed(trail):
                if c != "act":
                    break
                run += 1
            if alias.startswith("act.") and run >= 3:
                out["additionalContext"] += (
                    f" — ACT RUN: {run} act calls in a row with no observe or orient between them. "
                    "Look before the next act: cd " + str(ROOT) + " && python3 tools/matrix.py orient.probe")
        except (OSError, ValueError):
            pass  # the trail is a warning, never a gate
        stalls = sorted((ROOT / ".claude/.matrix-stalls").glob("*.json"))
        if stalls:
            out["additionalContext"] += (
                f" — OPEN MATRIX STALL ({len(stalls)}): a Matrix call breached the 10 s cap. Diagnose why the alias "
                f"stalled and improve it before other work: cd {ROOT} && python3 tools/matrix.py orient.stall")
        print(json.dumps({"hookSpecificOutput": out}))
    except Exception as exc:
        # Fail closed where it matters, loud everywhere. An error is logged to .claude/.matrix-errors
        # with its reason. In enforce mode a call the hook could not judge is denied, not allowed:
        # a gated native tool must not slip through because the hook broke. In warn or name mode the
        # call proceeds, as before, so this changes nothing until enforce is turned on.
        try:
            errs = ROOT / ".claude/.matrix-errors"
            errs.parent.mkdir(exist_ok=True)
            with errs.open("a", encoding="utf-8") as fh:
                fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\t{type(exc).__name__}: {exc}\n")
        except OSError:
            pass
        mode_now = os.environ.get("MATRIX_MODE") or ""
        if not mode_now:
            try:
                mode_now = json.loads((ROOT / ".claude/cardinal-map.json").read_text(encoding="utf-8")).get("mode", "name")
            except Exception:
                mode_now = "name"
        if mode_now == "enforce" and not (ROOT / ".claude/.matrix-off").exists():
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"The Matrix could not judge this call ({type(exc).__name__}). "
                                            "Fail-closed in enforce mode. Check .claude/.matrix-errors; "
                                            "kill switch: touch .claude/.matrix-off"}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
