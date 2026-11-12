#!/usr/bin/env bash
# no-poll.sh: PreToolUse gate. Blocks reads that poll PR status, CI, or the
# notification queue. PR and CI events arrive on their own; polling is banned.
# Exit 2 blocks the call and returns the message to the model.
input=$(cat)
tool=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_name",""))' 2>/dev/null)
case "$tool" in
  ReadNotifications \
  | mcp__github__pull_request_read \
  | mcp__github__get_check_run \
  | mcp__github__actions_get \
  | mcp__github__actions_list \
  | mcp__claude-code-remote__list_events \
  | mcp__claude-code-remote__get_event)
    echo "Polling is disabled in this repo. PR and CI events arrive on their own, so do not read them. Blocked: $tool" >&2
    exit 2 ;;
esac
exit 0
