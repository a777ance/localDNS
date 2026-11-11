#!/usr/bin/env bash
# PreToolUse router: sends tool calls through repo-owned versions.
# Map: .claude/tool-aliases.json (empty = no-op).
#   Bash rule, action "rewrite": regex-replaces the command string, then allows.
#   Any rule, action "block":    denies the call and tells Claude the replacement.
# Built-in tool names cannot be renamed by a hook; this routes the call instead.
# Break-glass: if .claude/.alias-off exists, enforcement is off (exit 0).
# Minimum toolset: tools named in .claude/mvp-toolset.json are always allowed.
set -u
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
[ -f "$ROOT/.claude/.alias-off" ] && exit 0
MAP="$ROOT/.claude/tool-aliases.json"
MVP="$ROOT/.claude/mvp-toolset.json"
[ -f "$MAP" ] || exit 0

PAYLOAD=$(cat)
PY=$(cat <<'PY'
import json, re, sys

payload = json.loads(sys.stdin.read())
tool = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {}) or {}
rules = json.load(open(sys.argv[1])).get("aliases", [])
try:
    mvp = set(json.load(open(sys.argv[2])).get("tools", []))
except (OSError, ValueError):
    mvp = set()

if tool in mvp:
    sys.exit(0)

for rule in rules:
    if rule.get("tool") != tool:
        continue
    if rule.get("action") == "rewrite" and tool == "Bash":
        cmd = tool_input.get("command", "")
        if re.search(rule["match"], cmd):
            new_cmd = re.sub(rule["match"], rule["replace"], cmd)
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"alias: {rule.get('name', 'rewrite')}",
                "updatedInput": {**tool_input, "command": new_cmd}}}))
            sys.exit(0)
    elif rule.get("action") == "block":
        if "match" in rule and not re.search(rule["match"], json.dumps(tool_input)):
            continue
        print(rule.get("message", f"{tool} is routed to a repo version."), file=sys.stderr)
        sys.exit(2)
sys.exit(0)
PY
)
printf '%s' "$PAYLOAD" | python3 -c "$PY" "$MAP" "$MVP"
