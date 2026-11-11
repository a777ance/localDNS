#!/usr/bin/env python3
"""check-telepathy.py — end-to-end test of the telepathy mailbox and its watcher.

In a throwaway mailbox directory (TELEPATHY_DIR), with two named sessions:
  send -> inbox -> read -> mark_done over the MCP server's JSON-RPC stdio, and
  the watcher (tools/telepathy/watch.py) must print NEW for an arrival within 2 s.
The real mailbox (~/.local/state/telepathy) is never touched.

Exit 0 when clean, 1 otherwise. Linux only (the watcher uses inotify).
"""
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DIR = Path(__file__).resolve().parent / "telepathy"
FAILS = []


def check(name, ok, detail=""):
    if not ok:
        FAILS.append(f"{name}{': ' + str(detail)[:160] if detail else ''}")


def call(env, name, tool, **arguments):
    """One tools/call against a fresh MCP server process acting as session `name`."""
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}}
    r = subprocess.run([sys.executable, str(DIR / "telepathy_mcp.py")], input=json.dumps(req) + "\n",
                       capture_output=True, text=True, timeout=10, env={**env, "TELEPATHY_NAME": name})
    result = json.loads(r.stdout)["result"]
    text = result["content"][0]["text"]
    return (None, text) if result.get("isError") else (json.loads(text), "")


def wait_line(proc, want, seconds):
    """Read the watcher's stdout until a line contains `want`, or the deadline passes."""
    deadline, seen = time.time() + seconds, ""
    while time.time() < deadline:
        ready, _, _ = select.select([proc.stdout], [], [], max(0, deadline - time.time()))
        if not ready:
            break
        line = proc.stdout.readline()
        seen += line
        if want in line:
            return True, seen
    return False, seen


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="telepathy-e2e-") as tmp:
        env = {**os.environ, "TELEPATHY_DIR": tmp, "PYTHONUNBUFFERED": "1"}
        watcher = subprocess.Popen([sys.executable, str(DIR / "watch.py"), "bob"], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, env=env, cwd=DIR)
        try:
            armed, seen = wait_line(watcher, "armed", 5)
            check("watcher arms", armed, seen)
            t0 = time.time()  # measured from before the send, so it includes the sender's start-up
            sent, err = call(env, "alice", "send", to="bob", subject="hello", body="first message")
            check("send", sent and sent.get("to") == "bob", err)
            mid = sent["sent"] if sent else "none"
            woke, seen = wait_line(watcher, f"NEW {mid}", 2)
            check("watcher prints NEW within 2 s", woke, seen or "nothing printed")
            took = time.time() - t0
        finally:
            watcher.kill()
            watcher.wait()
        inbox, err = call(env, "bob", "inbox")
        check("inbox lists it unread", inbox and [m["id"] for m in inbox["messages"]] == [mid], err or inbox)
        msg, err = call(env, "bob", "read", id=mid)
        check("read returns the body", msg and msg.get("body") == "first message" and msg.get("from") == "alice", err)
        done, err = call(env, "bob", "mark_done", id=mid)
        check("mark_done", done and done.get("done") == mid, err)
        inbox, _ = call(env, "bob", "inbox")
        check("inbox is empty afterwards", inbox and inbox["messages"] == [], inbox)
        everything, _ = call(env, "bob", "inbox", unread_only=False)
        check("the message is kept as done", everything and everything["messages"][0]["status"] == "done", everything)
        check("alice cannot read bob's mail", call(env, "alice", "read", id=mid)[0] is None)
        check("a bad mailbox name is refused", call(env, "alice", "send", to="../x", body="b")[0] is None)
    for f in FAILS:
        print("FAIL", f)
    if not FAILS:
        print(f"ok   telepathy end to end: send, inbox, read, mark done; send to wake took {took:.2f}s")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
