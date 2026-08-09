#!/usr/bin/env python3
"""The weave: see who holds the eye, and LICENCE work to exactly one Norn.

WHY (docs/architecture/norns.md §5)
-----------------------------------
Concurrent sessions weave `Yggdrasil` and cannot see each other — `ListAgents` returns
nothing and the CCR server exposes `create_session` with no `send_message`. Git catches
collisions; nothing catches two Norns handed the same thread. On 2026-08-08 a session was
spawned to "archive the doom drawer" minutes after the drawer had been built and pushed.

Redundancy is right for the reasoning and wrong for the writing. Many polymerases
transcribe one gene at once because the template is READ-ONLY. Norns write. Where the
template IS written, life licenses each origin once per cell cycle — and DESTROYS the
licence when it fires, so it cannot outlive its purpose.

THE MECHANISM — one file per claim, git is the mutex
-----------------------------------------------------
Two Norns claiming DIFFERENT work touch different paths and never conflict. Two claiming
the SAME work collide on one path, and exactly one push fast-forwards. That push IS the
licence. A shared table would conflict on every claim, which trains people to skip it.

THE LEASE — a lock that cannot outlive its holder
--------------------------------------------------
A licence only its holder can release is a lock with no lease: a session that ends while
holding one locks that item forever. So a licence goes STALE when BOTH hold:
  * older than --lease hours (default 4), and
  * its holder has committed nothing to Yggdrasil since claiming it.
The second test prevents a false break and needs no external API: every commit carries a
`Claude-Session:` trailer, so git alone answers "has this holder done anything since?" A
busy holder never goes stale however long the work runs; only a silent one ages out.

EXCHANGE — push and pull, and why they differ
----------------------------------------------
  * PUSH (`--hand ITEM --to <session>`) is always safe: the holder consents by definition,
    so a hand-off needs no liveness test and no permission beyond holding the licence.
  * PULL (`--take ITEM --reason ...`) is only safe when the holder is demonstrably gone.
    Taking live work from a working Norn is the one thing this system must never permit,
    because it would make every licence advisory. So --take refuses unless the lease has
    expired AND the holder has been silent, and it records who took it and why.

USAGE
-----
    python3 tools/weave.py                                  # eye, licences, queue
    python3 tools/weave.py --norns                          # who has been weaving lately
    python3 tools/weave.py --claim "item" --lane skuld
    python3 tools/weave.py --renew "item"                   # heartbeat a long, quiet job
    python3 tools/weave.py --release "item"                 # done with it
    python3 tools/weave.py --hand "item" --to session_XYZ   # push: give it away
    python3 tools/weave.py --take "item" --reason "holder ended"   # pull: only if stale

EXIT CODES
----------
    0  viewer ran, or the operation succeeded
    1  refused (held by a live Norn, dirty tree, not yours, or not yet stale)
"""

from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CLAIMS = REPO / "docs/weave/claims"
QUEUE = REPO / "docs/ai-cto/context.md"
BRANCH = "Yggdrasil"
LANES = ("urdr", "verdandi", "skuld")
LEASE_HOURS = 4.0
TS = "%Y-%m-%d %H:%M UTC"


def git(*a: str, timeout: int = 60) -> tuple[int, str]:
    try:
        r = subprocess.run(("git", "-C", str(REPO)) + a,
                           capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, str(e)
    return r.returncode, (r.stdout + r.stderr).strip()


def slug(t: str) -> str:
    return (re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60] or "claim")


def core(sid: str) -> str:
    """The identity shared by `cse_ABC`, `session_ABC` and a bare `ABC`.

    The environment hands a session id one way and the commit trailer writes it another;
    matching on the raw string would silently report every holder as inactive, which is
    the dangerous direction — it would make live licences look stale and breakable."""
    return re.sub(r"^(cse|session|sess)_", "", (sid or "").strip())


def me() -> str:
    return (os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
            or os.environ.get("CLAUDE_CODE_SESSION_ID")
            or os.environ.get("USER") or "unknown")


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def parse_ts(s: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(s.strip(), TS).replace(tzinfo=datetime.timezone.utc)
    except (ValueError, AttributeError):
        return None


def read(path: pathlib.Path) -> dict[str, str]:
    d: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.startswith("#"):
                k, _, v = line.partition(":")
                d[k.strip().lower()] = v.strip()
    return d


def remote_claim(rel: str) -> dict[str, str]:
    code, body = git("show", f"origin/{BRANCH}:{rel}")
    if code != 0:
        return {}
    d: dict[str, str] = {}
    for line in body.splitlines():
        if ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            d[k.strip().lower()] = v.strip()
    return d


def holder_active_since(session: str, since: datetime.datetime) -> bool:
    """Has this holder committed to Yggdrasil since it claimed? Liveness, from git only."""
    cid = core(session)
    if not cid:
        return False
    code, out = git("log", f"origin/{BRANCH}", f'--since={since.strftime("%Y-%m-%d %H:%M:%S")} +0000',
                    "--format=%B")
    return code == 0 and cid in out


def staleness(c: dict[str, str], lease: float) -> tuple[bool, str]:
    """(is_stale, human reason). Stale needs BOTH age and RECENT silence.

    The silence window is the LEASE, not "since the claim". Checking activity since the
    claim would let one commit keep a licence alive forever: a Norn that claimed, pushed
    once, and then ended would never age out, and the lock would outlive it — the exact
    bug the lease exists to remove. What keeps a licence is a heartbeat INSIDE the window,
    which is what --renew is for."""
    claimed = parse_ts(c.get("claimed", ""))
    if not claimed:
        return False, "claim has no readable timestamp — not takeable"
    hrs = (now() - claimed).total_seconds() / 3600.0
    if hrs < lease:
        return False, f"held {hrs:.1f}h, lease {lease:.0f}h — not yet expired"
    window = now() - datetime.timedelta(hours=lease)
    if holder_active_since(c.get("session", ""), window):
        return False, f"held {hrs:.1f}h BUT the holder committed within the last {lease:.0f}h — alive"
    return True, f"held {hrs:.1f}h, no commits from the holder in the last {lease:.0f}h — stale"


def all_claims() -> list[tuple[str, dict[str, str]]]:
    if not CLAIMS.is_dir():
        return []
    return sorted(((p.stem, read(p)) for p in CLAIMS.glob("*.md") if p.name != "README.md"),
                  key=lambda kv: kv[1].get("claimed", ""), reverse=True)


def dirty_excluding(rel: str) -> list[str]:
    _, out = git("status", "--porcelain")
    return [l for l in out.splitlines() if l.strip() and rel not in l]


def write_and_push(path: pathlib.Path, rel: str, fields: dict[str, str],
                   title: str, msg: str) -> int:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    body = f"# {title}\n\n" + "".join(f"{k}: {v}\n" for k, v in fields.items())
    path.write_text(body, encoding="utf-8")
    git("add", "--", rel)
    code, out = git("commit", "-q", "-m", msg, "--", rel)
    if code != 0 and "nothing to commit" not in out:
        print(f"could not commit: {out[:200]}")
        return 1
    code, out = git("push", "origin", f"{BRANCH}:{BRANCH}")
    if code != 0:
        git("fetch", "origin", BRANCH, "--quiet")
        after = remote_claim(rel)
        if after and core(after.get("session", "")) != core(me()):
            git("reset", "--hard", f"origin/{BRANCH}")
            print(f"REFUSED — lost the race: now held by {after.get('session')}.")
            return 1
        print(f"push rejected (the eye moved). Rebase and retry:\n"
              f"  git fetch origin {BRANCH} && git rebase origin/{BRANCH}")
        return 1
    return 0


def op(item: str, mode: str, lane: str | None, to: str | None,
       reason: str | None, lease: float) -> int:
    name = f"{slug(item)}.md"
    path, rel = CLAIMS / name, f"docs/weave/claims/{slug(item)}.md"
    git("fetch", "origin", BRANCH, "--quiet")
    cur = remote_claim(rel)
    held = cur.get("status") == "held"
    holder = cur.get("session", "")
    mine = core(holder) == core(me())

    if mode == "claim":
        if held and not mine:
            stale, why = staleness(cur, lease)
            print(f"REFUSED — '{item}' is licensed to {holder}.")
            print(f"  {why}")
            print("  A licensed origin does not re-fire. Pick another item"
                  + (", or take it:  --take \"" + item + "\" --reason \"...\"" if stale else "."))
            return 1
        blocking = dirty_excluding(rel)
        if blocking:
            print("REFUSED — the tree is dirty, so the work already started.")
            print("  The rule is CLAIM BEFORE THE WORK. Commit or stash first:")
            for l in blocking[:6]:
                print(f"    {l}")
            return 1
        f = {"item": item, "lane": lane or cur.get("lane", "unstated"),
             "session": me(), "status": "held", "claimed": now().strftime(TS)}
        rc = write_and_push(path, rel, f, item, f"weave: claim — {item}")
        if rc == 0:
            print(f"LICENSED — {item}\n  lane: {f['lane']}   session: {me()}")
        return rc

    if not held:
        print(f"'{item}' is not currently held — nothing to {mode}.")
        return 1

    if mode == "renew":
        if not mine:
            print(f"REFUSED — held by {holder}, not you.")
            return 1
        f = dict(cur); f["claimed"] = now().strftime(TS)
        rc = write_and_push(path, rel, f, item, f"weave: renew — {item}")
        if rc == 0:
            print(f"RENEWED — {item}\n  lease restarts now ({lease:.0f}h)")
        return rc

    if mode == "release":
        if not mine:
            print(f"REFUSED — held by {holder}, not you. Not yours to release.")
            print("  If that Norn has ended, use --take with a reason instead.")
            return 1
        f = dict(cur); f["status"] = "released"; f["released"] = now().strftime(TS)
        rc = write_and_push(path, rel, f, item, f"weave: release — {item}")
        if rc == 0:
            print(f"RELEASED — {item}")
        return rc

    if mode == "hand":                       # PUSH — the holder consents, so always safe
        if not mine:
            print(f"REFUSED — held by {holder}, not you. You cannot give away another's licence.")
            return 1
        if not to:
            print("--hand needs --to <session>")
            return 1
        f = dict(cur)
        f.update({"session": to, "status": "held", "claimed": now().strftime(TS),
                  "handed-from": holder, "handed-at": now().strftime(TS)})
        rc = write_and_push(path, rel, f, item, f"weave: hand — {item} -> {to}")
        if rc == 0:
            print(f"HANDED — {item}\n  {holder}  ->  {to}\n"
                  f"  Their lease starts now. You no longer hold it.")
        return rc

    if mode == "take":                       # PULL — only from a holder who is gone
        if mine:
            print("You already hold it. Use --release, or --hand to give it away.")
            return 1
        if not reason:
            print("--take needs --reason \"why\" — a break must be answerable later.")
            return 1
        stale, why = staleness(cur, lease)
        if not stale:
            print(f"REFUSED — '{item}' is still live with {holder}.")
            print(f"  {why}")
            print("  Taking work from a working Norn would make every licence advisory.")
            print("  Ask the founder to reassign it, or wait for the lease to expire.")
            return 1
        f = dict(cur)
        f.update({"session": me(), "status": "held", "claimed": now().strftime(TS),
                  "taken-from": holder, "taken-at": now().strftime(TS), "taken-because": reason})
        rc = write_and_push(path, rel, f, item, f"weave: take — {item} (was {holder}): {reason}")
        if rc == 0:
            print(f"TAKEN — {item}\n  was: {holder}  ({why})\n  now: {me()}\n  reason: {reason}")
        return rc

    print(f"unknown mode {mode}")
    return 1


def norns(hours: int) -> int:
    """Who has been weaving lately — the roster, derived from commit trailers alone."""
    git("fetch", "origin", BRANCH, "--quiet")
    code, out = git("log", f"origin/{BRANCH}", f"--since={hours} hours ago",
                    "--format=%H%x01%an%x01%ad%x01%B%x02", "--date=format:%m-%d %H:%M")
    seen: dict[str, list[str]] = {}
    for rec in out.split("\x02"):
        parts = rec.strip().split("\x01")
        if len(parts) < 4:
            continue
        m = re.search(r"Claude-Session:\s*\S*?(?:session_|cse_)?([A-Za-z0-9]{10,})", parts[3])
        sid = m.group(1) if m else "(no trailer)"
        seen.setdefault(sid, []).append(parts[2])
    print(f"\n── Norns active on {BRANCH} in the last {hours}h ──")
    if not seen:
        print("  (none)")
    for sid, times in sorted(seen.items(), key=lambda kv: len(kv[1]), reverse=True):
        mark = "  <- you" if core(sid) == core(me()) else ""
        print(f"  {sid[:26]:28} {len(times):3} commit(s)   last {times[0]}{mark}")
    print("\n  A holder that appears here is ALIVE — its licence cannot be taken.\n")
    return 0


def view(local: bool, n: int, lease: float) -> int:
    if not local:
        git("fetch", "origin", BRANCH, "--quiet")
    ref = f"origin/{BRANCH}"
    _, tip = git("rev-parse", "--short", ref)
    print(f"\n── the eye ──\n  {ref} @ {tip or '?'}")
    _, counts = git("rev-list", "--left-right", "--count", f"{ref}...{BRANCH}")
    p = counts.split()
    if len(p) == 2:
        behind, ahead = p
        if behind == ahead == "0":
            print("  you hold it — local and remote agree")
        else:
            if behind != "0":
                print(f"  ANOTHER NORN MOVED IT — {behind} behind. fetch and rebase before writing.")
            if ahead != "0":
                print(f"  {ahead} unpushed commit(s) — hand the eye back when done.")

    print(f"\n── recent weave ({ref}) ──")
    _, log = git("log", f"-{n}", "--format=%ad  %h  %s", "--date=format:%m-%d %H:%M", ref)
    print("\n".join(f"  {l}" for l in log.splitlines()) if log else "  (none)")

    print("\n── licences — docs/weave/claims/ ──")
    cl = all_claims()
    if not cl:
        print("  (nothing licensed)")
    for nm, c in cl:
        if c.get("status") == "held":
            stale, why = staleness(c, lease)
            print(f"  {'STALE   ' if stale else 'HELD    '} {c.get('item', nm)}")
            print(f"           lane={c.get('lane','?')}  session={c.get('session','?')}")
            print(f"           {why}")
            if stale:
                print(f"           takeable:  --take \"{c.get('item', nm)}\" --reason \"...\"")
        else:
            print(f"  released {c.get('item', nm)}")

    print("\n── queue — docs/ai-cto/context.md ──")
    if QUEUE.exists():
        m = re.search(r"## Default next actions(.*?)\n---", QUEUE.read_text(encoding="utf-8"), re.S)
        items = [l.rstrip() for l in (m.group(1).splitlines() if m else [])
                 if re.match(r"^\s*\d+\.\s", l) or l.strip().startswith("**")]
        print("\n".join(f"  {i}" for i in items) if items else "  (empty)")

    print('\n  claim before you write:  --claim "<item>" --lane <urdr|verdandi|skuld>')
    print("  give it away: --hand \"<item>\" --to <session>   |   who is alive: --norns\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for f in ("claim", "release", "renew", "hand", "take"):
        ap.add_argument(f"--{f}", metavar="ITEM")
    ap.add_argument("--to", metavar="SESSION")
    ap.add_argument("--reason", metavar="WHY")
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--lease", type=float, default=LEASE_HOURS)
    ap.add_argument("--norns", action="store_true")
    ap.add_argument("--hours", type=int, default=12)
    ap.add_argument("--local", action="store_true")
    ap.add_argument("-n", type=int, default=8)
    a = ap.parse_args()

    modes = [(m, getattr(a, m)) for m in ("claim", "release", "renew", "hand", "take")
             if getattr(a, m)]
    if len(modes) > 1:
        print("pick one operation")
        return 1
    if a.norns:
        return norns(a.hours)
    if modes:
        mode, item = modes[0]
        return op(item, mode, a.lane, a.to, a.reason, a.lease)
    return view(a.local, a.n, a.lease)


if __name__ == "__main__":
    raise SystemExit(main())
