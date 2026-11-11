#!/usr/bin/env python3
"""watch.py — event-driven mailbox watcher for telepathy. NO POLLING.

Blocks in the kernel on inotify (read() sleeps until the filesystem reports an
event) and prints one line per message that lands in this session's `new/`
directory. Intended to run under Claude Code's Monitor tool, where each stdout
line becomes a wake-up. Standard library only (ctypes -> libc inotify).

Usage: python3 watch.py [mailbox-name]     (default: same name rules as telepathy_mcp.py)
"""
import ctypes
import ctypes.util
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import telepathy_mcp as tp  # reuses ROOT and name rules; no duplicate logic

IN_MOVED_TO = 0x00000080
IN_CLOSE_WRITE = 0x00000008
IN_CREATE = 0x00000100
EVENT_HDR = struct.Struct("iIII")  # wd, mask, cookie, len


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else tp.my_name()
    new_dir = tp.box(name) / "new"
    libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)
    fd = libc.inotify_init1(0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "inotify_init1 failed")
    wd = libc.inotify_add_watch(fd, str(new_dir).encode(), IN_MOVED_TO | IN_CLOSE_WRITE | IN_CREATE)
    if wd < 0:
        raise OSError(ctypes.get_errno(), "inotify_add_watch failed")
    print(f"telepathy watch: mailbox '{name}' armed on {new_dir}", flush=True)

    # Report anything already waiting before we started.
    for f in sorted(new_dir.glob("*.json")):
        print(f"NEW {f.stem} (already waiting)", flush=True)

    while True:
        buf = os.read(fd, 4096)  # blocks until the kernel has an event
        off = 0
        while off < len(buf):
            _wd, _mask, _cookie, ln = EVENT_HDR.unpack_from(buf, off)
            off += EVENT_HDR.size
            fname = buf[off:off + ln].rstrip(b"\0").decode(errors="replace")
            off += ln
            if fname.endswith(".json"):
                print(f"NEW {fname[:-5]} from mailbox '{name}'", flush=True)


if __name__ == "__main__":
    main()
