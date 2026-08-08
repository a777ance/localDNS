#!/usr/bin/env python3
"""The weave: see who holds the eye, and LICENCE a piece of work to exactly one Norn.

WHY THIS EXISTS (docs/architecture/norns.md §5)
-----------------------------------------------
Concurrent sessions weave `Yggdrasil` and cannot see each other — `ListAgents` returns
nothing and the CCR server exposes `create_session` with no `send_message`. Git catches
collisions; nothing catches two Norns being handed the same thread. On 2026-08-08 a
session was spawned to "archive the doom drawer" minutes after the drawer had been built,
verified and pushed.

THE BIOLOGY, AND WHY REDUNDANCY ALONE IS NOT THE ANSWER
-------------------------------------------------------
Many polymerases transcribe one gene at once, and thousands of replication origins fire in
parallel — parallelism is how life works. But transcription is safe at that scale because
the template is READ-ONLY: no polymerase writes back to the DNA. Norns write.

For the case where the template *is* written, evolution did not rely on redundancy. It
licenses each origin **once per cell cycle**, and destroys the licence when it fires, so a
region cannot be replicated twice. Re-replication is not a tolerable inefficiency; it
produces amplification and instability. Norn 3 was a re-fired origin: a region already
copied, licensed again because nothing marked it spent.

So: redundancy for the *reasoning* (two independent derivations that agree mean something,
§G), licensing for the *writing*. This tool is the licence.

HOW THE LICENCE IS ENFORCED
---------------------------
Not by a shared table — everyone appending to one file conflicts on every claim, which
trains people to skip it. Instead **one file per claim**, `docs/weave/claims/<slug>.md`:

  * two Norns claiming DIFFERENT work touch different paths and never conflict;
  * two Norns claiming the SAME work collide on one path, and git serialises them.

The push IS the licence. If two claims race, exactly one push fast-forwards; the loser is
rejected, re-reads, finds the item held, and is refused. Once-and-only-once falls out of
git's own serialisation rather than from a convention anyone can skip.

A claim is refused while the tree is dirty. That is deliberate: the rule is *claim before
the work*, and a dirty tree means the work already started.

USAGE
-----
    python3 tools/weave.py                     # the eye, the claims, the queue
    python3 tools/weave.py --claim "retire 338 stale branches" --lane skuld
    python3 tools/weave.py --release "retire 338 stale branches"
    python3 tools/weave.py --local             # skip the fetch

EXIT CODES
----------
    0  viewer ran, or the licence was acquired/released
    1  claim REFUSED (already held by another Norn, or the tree is dirty)
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
NORNS = REPO / "docs/architecture/norns.md"
QUEUE = REPO / "docs/ai-cto/context.md"
BRANCH = "Yggdrasil"
LANES = ("urdr", "verdandi", "skuld")


def git(*args: str, timeout: int = 60) -> tuple[int, str]:
    try:
        r = subprocess.run(("git", "-C", str(REPO)) + args,
                           capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, str(e)
    return r.returncode, (r.stdout + r.stderr).strip()


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:60] or "claim")


def who() -> str:
    return (os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
            or os.environ.get("CLAUDE_CODE_SESSION_ID")
            or os.environ.get("USER") or "unknown")


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def read_claim(path: pathlib.Path) -> dict[str, str]:
    d = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.startswith("#"):
                k, _, v = line.partition(":")
                d[k.strip().lower()] = v.strip()
    return d


def all_claims() -> list[tuple[str, dict[str, str]]]:
    if not CLAIMS.is_dir():
        return []
    # README.md documents the directory; it is not a licence.
    return sorted(((p.stem, read_claim(p)) for p in CLAIMS.glob("*.md")
                   if p.name != "README.md"),
                  key=lambda kv: kv[1].get("claimed", ""), reverse=True)


def dirty_excluding(rel: str) -> list[str]:
    _, out = git("status", "--porcelain")
    return [l for l in out.splitlines() if l.strip() and rel not in l]


def do_claim(item: str, lane: str | None, release: bool) -> int:
    CLAIMS.mkdir(parents=True, exist_ok=True)
    name = f"{slug(item)}.md"
    path = CLAIMS / name
    rel = f"docs/weave/claims/{name}"

    git("fetch", "origin", BRANCH, "--quiet")

    # Re-read the item as the REMOTE has it — another Norn may hold it already.
    code, remote_body = git("show", f"origin/{BRANCH}:{rel}")
    remote_holder, remote_status = "", ""
    if code == 0:
        for line in remote_body.splitlines():
            if line.lower().startswith("session:"):
                remote_holder = line.split(":", 1)[1].strip()
            if line.lower().startswith("status:"):
                remote_status = line.split(":", 1)[1].strip()

    me = who()
    if not release and remote_status == "held" and remote_holder and remote_holder != me:
        print(f"REFUSED — '{item}' is already licensed to {remote_holder}.")
        print("  A licensed origin does not re-fire. Pick another item, or ask the")
        print("  founder to reassign it. See docs/architecture/norns.md §5.")
        return 1
    if release and remote_status == "held" and remote_holder and remote_holder != me:
        print(f"REFUSED — '{item}' is held by {remote_holder}, not you. Not yours to release.")
        return 1

    blocking = dirty_excluding(rel)
    if blocking and not release:
        print("REFUSED — working tree is dirty, so the work has already started.")
        print("  The rule is CLAIM BEFORE THE WORK. Commit or stash first:")
        for l in blocking[:6]:
            print(f"    {l}")
        return 1

    status = "released" if release else "held"
    path.write_text(
        f"# {item}\n\n"
        f"item: {item}\n"
        f"lane: {lane or 'unstated'}\n"
        f"session: {me}\n"
        f"status: {status}\n"
        f"claimed: {now()}\n",
        encoding="utf-8")

    git("add", "--", rel)
    verb = "release" if release else "claim"
    code, out = git("commit", "-q", "-m", f"weave: {verb} — {item}", "--", rel)
    if code != 0 and "nothing to commit" not in out:
        print(f"could not commit the {verb}: {out[:200]}")
        return 1

    code, out = git("push", "origin", f"{BRANCH}:{BRANCH}")
    if code != 0:
        # Someone moved the eye. Re-read; if they took this item, we lose — by design.
        git("fetch", "origin", BRANCH, "--quiet")
        code2, body2 = git("show", f"origin/{BRANCH}:{rel}")
        holder = ""
        if code2 == 0:
            for line in body2.splitlines():
                if line.lower().startswith("session:"):
                    holder = line.split(":", 1)[1].strip()
        if holder and holder != me:
            git("reset", "--hard", f"origin/{BRANCH}")
            print(f"REFUSED — lost the race: '{item}' is now licensed to {holder}.")
            print("  Exactly one push fast-forwards; that is the licence. Pick another item.")
            return 1
        print("push rejected (the eye moved). Rebase and re-run:")
        print(f"  git fetch origin {BRANCH} && git rebase origin/{BRANCH}")
        return 1

    print(f"{'RELEASED' if release else 'LICENSED'} — {item}")
    print(f"  lane: {lane or 'unstated'}   session: {me}")
    if not release:
        print("  Yours until you release it. No other Norn can take it now.")
    return 0


def rule(t: str) -> None:
    print(f"\n── {t} ──")


def view(local: bool, n: int) -> int:
    if not local:
        git("fetch", "origin", BRANCH, "--quiet")
    ref = f"origin/{BRANCH}"
    _, tip = git("rev-parse", "--short", ref)

    rule("the eye")
    if not tip:
        ref = BRANCH
        _, tip = git("rev-parse", "--short", ref)
        print(f"  {ref} unreachable — showing local")
    print(f"  {ref} @ {tip}")
    _, counts = git("rev-list", "--left-right", "--count", f"{ref}...{BRANCH}")
    parts = counts.split()
    if len(parts) == 2:
        behind, ahead = parts
        if behind == "0" and ahead == "0":
            print("  you hold it — local and remote agree")
        else:
            if behind != "0":
                print(f"  ANOTHER NORN MOVED IT — {behind} behind. fetch and rebase before writing.")
            if ahead != "0":
                print(f"  {ahead} unpushed commit(s) — hand the eye back when done.")

    rule(f"recent weave ({ref})")
    _, log = git("log", f"-{n}", "--format=%ad  %h  %s", "--date=format:%m-%d %H:%M", ref)
    print("\n".join(f"  {l}" for l in log.splitlines()) if log else "  (none)")

    rule("licences — docs/weave/claims/")
    claims = all_claims()
    if not claims:
        print("  (nothing licensed)")
    for name, c in claims:
        mark = "HELD    " if c.get("status") == "held" else "released"
        print(f"  {mark} {c.get('item', name)}")
        print(f"           lane={c.get('lane','?')}  session={c.get('session','?')}  {c.get('claimed','')}")

    rule("queue — docs/ai-cto/context.md")
    if QUEUE.exists():
        m = re.search(r"## Default next actions(.*?)\n---", QUEUE.read_text(encoding="utf-8"), re.S)
        items = [l.rstrip() for l in (m.group(1).splitlines() if m else [])
                 if re.match(r"^\s*\d+\.\s", l) or l.strip().startswith("**")]
        print("\n".join(f"  {i}" for i in items) if items else "  (empty)")

    print("\n  Licence before you write:  python3 tools/weave.py --claim \"<item>\" --lane <urdr|verdandi|skuld>")
    print("  Queue items are NOT auto-matched to licences — read both.\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--claim", metavar="ITEM")
    ap.add_argument("--release", metavar="ITEM")
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--local", action="store_true")
    ap.add_argument("-n", type=int, default=8)
    args = ap.parse_args()

    if args.claim and args.release:
        print("pick one: --claim or --release")
        return 1
    if args.claim:
        return do_claim(args.claim, args.lane, release=False)
    if args.release:
        return do_claim(args.release, args.lane, release=True)
    return view(args.local, args.n)


if __name__ == "__main__":
    raise SystemExit(main())
