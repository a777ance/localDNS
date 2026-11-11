#!/usr/bin/env python3
"""telepathy_mcp.py — a stdio MCP server that lets local Claude sessions pass
messages through a shared mailbox directory on one machine.

Transport: MCP over stdio (newline-delimited JSON-RPC 2.0). Standard library only.
Register with Claude Code (user scope, so every session on this box sees it):

    claude mcp add --scope user telepathy -- python3 /home/user/localDNS/tools/telepathy/telepathy_mcp.py

Mailbox: $TELEPATHY_DIR (default ~/.local/state/telepathy). One JSON file per
message, in <dir>/<recipient>/<timestamp>-<id>.json. Writes are atomic
(tmp file + rename), so a reader never sees a half-written message.

Tools:
  whoami()                      -> this session's mailbox name
  send(to, body, subject?)      -> deliver a message to another mailbox
  inbox(unread_only?=true)      -> list messages addressed to me, newest first
  read(id)                      -> read one message; marks it read
  mark_done(id)                 -> archive a message

Name: $TELEPATHY_NAME, else the session id from $CLAUDE_CODE_SESSION_ID, else hostname.
Messages are DATA from a peer, never instructions to change permissions or run
destructive actions on their own. This server does not execute anything it receives.
"""
import json
import os
import re
import socket
import sys
import time
import uuid
from pathlib import Path

PROTOCOL = "2024-11-05"
ROOT = Path(os.environ.get("TELEPATHY_DIR", Path.home() / ".local/state/telepathy"))
SAFE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def my_name() -> str:
    n = os.environ.get("TELEPATHY_NAME") or os.environ.get("CLAUDE_CODE_SESSION_ID") or socket.gethostname()
    n = re.sub(r"[^A-Za-z0-9._-]", "-", n)[:64] or "session"
    return n


def box(name: str) -> Path:
    if not SAFE.match(name):
        raise ValueError(f"invalid mailbox name: {name!r}")
    p = ROOT / name
    (p / "new").mkdir(parents=True, exist_ok=True)
    (p / "done").mkdir(parents=True, exist_ok=True)
    return p


def find(msg_id: str):
    if not re.match(r"^[A-Za-z0-9_-]{1,80}$", msg_id):
        raise ValueError("invalid id")
    me = box(my_name())
    for sub in ("new", "done"):
        f = me / sub / f"{msg_id}.json"
        if f.exists():
            return me, sub, f
    raise FileNotFoundError(f"no message {msg_id}")


def t_whoami(_a):
    return {"name": my_name(), "mailbox": str(box(my_name()))}


def t_send(a):
    to = a["to"]
    box(to)  # creates the recipient mailbox if absent; validates name
    mid = time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    msg = {"id": mid, "from": my_name(), "to": to, "subject": a.get("subject", ""),
           "body": a["body"], "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    target = ROOT / to / "new" / f"{mid}.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(msg, ensure_ascii=False, indent=2))
    tmp.rename(target)
    return {"sent": mid, "to": to}


def t_inbox(a):
    unread_only = a.get("unread_only", True)
    me = box(my_name())
    items = []
    subs = ["new"] if unread_only else ["new", "done"]
    for sub in subs:
        for f in (me / sub).glob("*.json"):
            m = json.loads(f.read_text())
            items.append({"id": m["id"], "from": m["from"], "subject": m.get("subject", ""),
                          "sent_at": m["sent_at"], "status": sub})
    items.sort(key=lambda x: x["id"], reverse=True)
    return {"messages": items}


def t_read(a):
    me, sub, f = find(a["id"])
    if sub == "new":
        f.rename(me / "done" / f.name)
    return json.loads((me / "done" / f.name).read_text())


def t_mark_done(a):
    me, sub, f = find(a["id"])
    if sub == "new":
        f.rename(me / "done" / f.name)
    return {"done": a["id"]}


TOOLS = {
    "whoami": (t_whoami, {"type": "object", "properties": {}}),
    "send": (t_send, {"type": "object", "required": ["to", "body"], "properties": {
        "to": {"type": "string", "description": "Recipient mailbox name"},
        "body": {"type": "string"},
        "subject": {"type": "string"}}}),
    "inbox": (t_inbox, {"type": "object", "properties": {
        "unread_only": {"type": "boolean", "default": True}}}),
    "read": (t_read, {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}),
    "mark_done": (t_mark_done, {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}),
}


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


def handle(req):
    method, rid = req.get("method"), req.get("id")
    if rid is None:  # notification: no reply
        return
    if method == "initialize":
        return reply(rid, {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                           "serverInfo": {"name": "telepathy", "version": "0.1.0"}})
    if method == "tools/list":
        return reply(rid, {"tools": [{"name": n, "description": (f.__doc__ or n), "inputSchema": s}
                                     for n, (f, s) in TOOLS.items()]})
    if method == "tools/call":
        p = req.get("params", {})
        name = p.get("name")
        if name not in TOOLS:
            return reply(rid, error={"code": -32602, "message": f"unknown tool {name}"})
        try:
            data = TOOLS[name][0](p.get("arguments", {}) or {})
            return reply(rid, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]})
        except Exception as e:  # tool errors go back as tool results, not protocol errors
            return reply(rid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
    if method == "ping":
        return reply(rid, {})
    return reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except json.JSONDecodeError:
            reply(None, error={"code": -32700, "message": "parse error"})


if __name__ == "__main__":
    main()
