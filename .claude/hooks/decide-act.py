#!/usr/bin/env python3
"""Stop hook — OODA "Decide → Act" gate.

If the reply that is ending this turn contains a **Decide** section with one or
more numbered items, block the stop and tell the agent to act on those items,
in order. A Decide list of zero (or no Decide section) lets the turn end.

Loop safety: when Claude Code re-enters the turn because of this hook, the
input carries stop_hook_active=true. This hook then allows the stop, so it
fires at most once per turn and cannot run away.

Reads the Stop hook JSON on stdin. Standard library only.
"""
import json
import re
import sys


def last_assistant_text(path):
    text = ""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = rec.get("message", rec)
                if msg.get("role") != "assistant" and rec.get("type") != "assistant":
                    continue
                content = msg.get("content", "")
                if isinstance(content, str):
                    parts = [content]
                else:
                    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                joined = "\n".join(p for p in parts if p)
                if joined:
                    text = joined  # keep the latest assistant text block group
    except OSError:
        return ""
    return text


def decide_items(text):
    """Return numbered items under a **Decide** heading (or 'Decide' line)."""
    m = re.search(r"^\W*Decide[ds]?\b.*$", text, re.MULTILINE)
    if not m:
        return []
    items = []
    started = False
    for line in text[m.end():].splitlines():
        if re.match(r"^\s*\d+\.\s+\S", line):
            items.append(line.strip())
            started = True
        elif started and line.strip() == "":
            break
        elif started and not re.match(r"^\s*\d+\.", line):
            break
    return items


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail open: never trap the session on malformed input
    if data.get("stop_hook_active"):
        return 0  # already continued once this turn; let it end
    items = decide_items(last_assistant_text(data.get("transcript_path", "")))
    if not items:
        return 0
    reason = (
        "OODA ACT: the Decide list has %d numbered item(s). Act on them now, in order, "
        "without choosing between them or asking first. Report each as Observed → Oriented "
        "→ Decided → Acted, one line each. Skip only an item the user has marked punt. "
        "Irreversible or outward-facing actions still need a confirm first.\n\n%s"
        % (len(items), "\n".join(items))
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
