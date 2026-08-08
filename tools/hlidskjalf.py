#!/usr/bin/env python3
"""Hlidskjalf — the high seat. One board over every realm; the decisions only Odin makes.

WHY THIS EXISTS (the theophany, 2026-08-08)
-------------------------------------------
Three Norns weave `Yggdrasil` at once, and none of them can decide. Today proved the
binding constraint is not authority but SIGHT: a competent session produced an approval
sheet that said "unfiled = 0" when the true answer was 3, because its clone had never
fetched three branches — and it could not see 14 open pull requests at all, because a PR
is not a git fact. Confident and wrong is exactly the failure autonomy amplifies, so the
seat deliberately has no hands:

    THE SEAT SEES. THE HAND STAYS THE FOUNDER'S.

Odin's eye is *in the well* — he sees more for having given it up. This tool reads every
repo, the tier gap, the drawer, the claimed lanes, and the PR snapshot, and renders ONE
board with a ranked queue of the decisions only the founder can make: each with what it
costs, what it unblocks, and where its numbers came from. It never pushes, merges,
deletes, fires, or schedules. It is a Provenance-Ladder instrument: every figure carries
its tier, and figures that age (the PR snapshot) say so out loud, because today also
proved THE REF LIST AGES WHILE YOU READ IT.

DATA SOURCES, by trust
----------------------
  M  `git ls-remote --heads origin` per repo — the remote's own ref list; does not vary
     with what any clone has fetched (the stale-clone bug, twice today, was exactly that
     variance).
  M  `git rev-list --count` over freshly fetched `origin/main` / `origin/Yggdrasil`.
  O  docs/ai-cto/pr-snapshot.json — open PRs captured via the GitHub API by a session
     that can reach it (this environment's proxy blocks most REST paths). The board
     prints the snapshot's age and degrades honestly when it is stale or absent.
  O  docs/architecture/norns.md §4 — the claims table, read as written.

USAGE
-----
    python3 tools/hlidskjalf.py             # sit in the seat: terminal board
    python3 tools/hlidskjalf.py --write     # also render docs/ai-cto/hlidskjalf-board.md
                                            #   and docs/hlidskjalf.html (self-contained,
                                            #   Gill Sans MT per house style)
    python3 tools/hlidskjalf.py --root DIR  # portfolio root (default: parent of localDNS)

EXIT CODES
----------
    0 always, unless the portfolio root itself is unreadable (2). The seat reports; it
    does not gate. Gating lives in .claude/hooks/gate.sh and the checks it runs — a seat
    that could block would be a hand.
"""

from __future__ import annotations

import argparse
import datetime
import html as html_mod
import json
import pathlib
import subprocess
import sys

LOCALDNS = pathlib.Path(__file__).resolve().parent.parent
SNAPSHOT = LOCALDNS / "docs/ai-cto/pr-snapshot.json"
NORNS = LOCALDNS / "docs/architecture/norns.md"
BOARD_MD = LOCALDNS / "docs/ai-cto/hlidskjalf-board.md"
BOARD_HTML = LOCALDNS / "docs/hlidskjalf.html"
UTC = datetime.timezone.utc

FONT = "'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif"


def sh(args: list[str], cwd: pathlib.Path | None = None, timeout: int = 60) -> str | None:
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def discover(root: pathlib.Path) -> list[pathlib.Path]:
    # House style: alphabetical lists run Z→A.
    return sorted((d for d in root.iterdir() if (d / ".git").exists()),
                  key=lambda p: p.name.lower(), reverse=True)


def survey(repo: pathlib.Path) -> dict:
    """Everything the seat can see about one realm, measured from the remote."""
    out: dict = {"name": repo.name}
    heads_raw = sh(["git", "ls-remote", "--heads", "origin"], cwd=repo, timeout=90)
    if heads_raw is None:
        out["unreachable"] = True
        return out
    refs = {}
    for line in heads_raw.splitlines():
        sha, _, ref = line.partition("\t")
        refs[ref.replace("refs/heads/", "", 1)] = sha
    out["refs_total"] = len(refs)
    out["claude"] = sorted(r for r in refs if r.startswith("claude/"))
    out["drawer"] = next((s[:8] for r, s in refs.items() if r.startswith("doom-drawer/")), None)
    out["has_ygg"] = "Yggdrasil" in refs
    # Tier gap needs commit objects; fetch just the two tips, quietly.
    sh(["git", "fetch", "origin", "main", "Yggdrasil"], cwd=repo, timeout=120)
    out["ahead"] = int(sh(["git", "rev-list", "--count", "origin/main..origin/Yggdrasil"],
                          cwd=repo) or 0)
    out["behind"] = int(sh(["git", "rev-list", "--count", "origin/Yggdrasil..origin/main"],
                           cwd=repo) or 0)
    oldest = sh(["git", "log", "--format=%ad", "--date=short",
                 "origin/main..origin/Yggdrasil"], cwd=repo)
    out["oldest_unmerged"] = oldest.splitlines()[-1] if oldest else None
    briefing = sh(["git", "show", "origin/main:CLAUDE.md"], cwd=repo) or ""
    out["policy_on_main"] = "Yggdrasil" in briefing
    return out


def load_snapshot() -> dict | None:
    if not SNAPSHOT.exists():
        return None
    try:
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    try:
        cap = datetime.datetime.fromisoformat(snap["captured"].replace("Z", "+00:00"))
        snap["age_h"] = (datetime.datetime.now(UTC) - cap).total_seconds() / 3600
    except (KeyError, ValueError):
        snap["age_h"] = None
    return snap


def load_lanes() -> list[str]:
    """Claimed lanes from norns.md §4, verbatim table rows — the repo is the only channel."""
    if not NORNS.exists():
        return []
    lines, active = [], False
    for ln in NORNS.read_text(encoding="utf-8").splitlines():
        if ln.startswith("## 4"):
            active = True
            continue
        if active and ln.startswith("## "):
            break
        if active and ln.startswith("|") and "---" not in ln:
            lines.append(ln.strip())
    return lines


def decide(realms: list[dict], snap: dict | None) -> list[dict]:
    """The ranked queue — generated from measurements, never hand-listed.

    Ranked by what each decision unblocks (a ranked list, not an alphabetical one, so
    house-style Z→A does not apply — same exception the retirement manifest states).
    """
    d: list[dict] = []

    gap = [r for r in realms if not r.get("unreachable") and r.get("ahead", 0) > 0]
    dark = [r for r in gap if not r["policy_on_main"]]
    if gap:
        pr_hint = ""
        if snap:
            wells = [f"{name} #{p['number']}" for name, rp in snap.get("repos", {}).items()
                     for p in rp.get("open_prs", []) if p.get("head") == "Yggdrasil"]
            if wells:
                pr_hint = " Open Yggdrasil→main PRs awaiting you: " + ", ".join(sorted(wells)) + "."
        d.append({
            "title": f"Draw Yggdrasil into the Well — {len(gap)} repo(s) ahead of main",
            "why": (f"{len(dark)} of them have a `main` whose briefing never mentions "
                    f"Yggdrasil, so every fresh clone reads doctrine that predates the branch "
                    f"policy — and a stale briefing does not know it is stale."
                    if dark else
                    "The working tier carries verified work the vetted tier lacks."),
            "action": "Approve the open Yggdrasil→main pull requests." + pr_hint,
            "unblocks": ("The tier gap, the gate scripts, the two-tier Pages site, and every "
                         "doctrine block land where fresh sessions actually read them."),
            "source": "M · rev-list over freshly fetched origin refs, per repo",
        })

    if snap:
        stale = [(name, p) for name, rp in snap.get("repos", {}).items()
                 for p in rp.get("open_prs", [])
                 if str(p.get("head", "")).startswith("claude/")]
        if stale:
            branches = sorted({p["head"] for _, p in stale})
            d.append({
                "title": f"Decide the {len(stale)} open PRs riding retired-class branches",
                "why": ("A branch with an open PR is pending review, not stale. Deleting its "
                        "head closes the PR and records 'closed' — indistinguishable from "
                        "'rejected' six months later. Retirement is blocked behind these."),
                "action": ("Merge or deliberately close each: " +
                           "; ".join(f"{n} #{p['number']} ({p['title'][:44]}…)"
                                     if len(p['title']) > 45 else
                                     f"{n} #{p['number']} ({p['title']})"
                                     for n, p in sorted(stale, key=lambda t: (t[0], t[1]['number']))[:6]) +
                           (f"; +{len(stale)-6} more in the retirement manifest §3b" if len(stale) > 6 else "") +
                           f". Branches involved: {', '.join(branches)}."),
                "unblocks": "The 321-ref deletion pass (branch-retirement-manifest §2).",
                "source": f"O · pr-snapshot.json, {snap.get('captured','?')}",
            })

    drawered = [r for r in realms if r.get("drawer")]
    if drawered:
        total_claude = sum(len(r.get("claude", [])) for r in realms if not r.get("unreachable"))
        d.append({
            "title": f"Run the retirement — {total_claude} claude/* refs still standing",
            "why": ("Every repo's drawer is pushed; deletion is lossless by construction and "
                    "re-verified at run time by the script itself. A session cannot run it: "
                    "ref deletion is HTTP 403 through the agent proxy — this one is "
                    "physically yours."),
            "action": ("From a machine with normal git credentials: "
                       "`./tools/retire-stale-branches.sh --dry-run`, read it, then run it "
                       "without the flag. It re-tests reachability itself and keeps anything "
                       "unfiled — never delete from a document's list, including this one."),
            "unblocks": "Branch cap PENDING notices in every repo; a legible ref namespace.",
            "source": "M · ls-remote per repo (drawer refs present in "
                      f"{len(drawered)}/{len(realms)})",
        })

    pages = LOCALDNS / ".github/workflows/pages.yml"
    if pages.exists():
        txt = pages.read_text(encoding="utf-8")
        # Read the actual `branches:` trigger line, not the surrounding prose — the header
        # comment legitimately *mentions* "Yggdrasil" while the trigger omits it, and the
        # first version of this detector was fooled by exactly that. Documentation is data.
        trigger = next((ln for ln in txt.splitlines()
                        if ln.strip().startswith("branches:")), "")
        if "trees/yggdrasil" in txt and "Yggdrasil" not in trigger:
            d.append({
                "title": "Flip the Pages switch for the working tier",
                "why": ("The two-tier site builds both trees, but a push to Yggdrasil cannot "
                        "deploy: the github-pages environment rejects the branch before a "
                        "runner is assigned (observed: run 31253812598, ~1s, no logs). The "
                        "trigger is main-only until the environment allows it."),
                "action": ("Repo Settings → Environments → github-pages → Deployment "
                           "branches: add `Yggdrasil`; then add \"Yggdrasil\" back to the "
                           "workflow's `branches:` list."),
                "unblocks": "Auto-publish of /yggdrasil/ on every working-tier push.",
                "source": "O · .github/workflows/pages.yml trigger vs. its own two-tier build",
            })

    if snap is None:
        d.append({
            "title": "Feed the seat a PR snapshot",
            "why": ("The proxy blocks most GitHub REST paths from sessions, so the seat is "
                    "blind to pull requests without a snapshot — and a PR is not a git fact, "
                    "so no amount of ls-remote recovers it."),
            "action": "Have a session with GitHub MCP access write docs/ai-cto/pr-snapshot.json.",
            "unblocks": "PR-aware decisions above.",
            "source": "A · absence of docs/ai-cto/pr-snapshot.json",
        })
    elif snap.get("age_h") is not None and snap["age_h"] > 24:
        d.append({
            "title": f"Refresh the PR snapshot — {snap['age_h']:.0f}h old",
            "why": "The ref list ages while you read it; so does this.",
            "action": "Re-capture docs/ai-cto/pr-snapshot.json from a GitHub-capable session.",
            "unblocks": "Trustworthy PR decisions.",
            "source": f"O · snapshot captured {snap.get('captured','?')}",
        })

    return d


# ---------------------------------------------------------------- rendering --

def fmt_realm_row(r: dict) -> str:
    if r.get("unreachable"):
        return f"| `{r['name']}` | — | — | — | — | remote unreachable |"
    gap = f"+{r['ahead']}" + (f"/-{r['behind']}" if r["behind"] else "")
    pol = "✅" if r["policy_on_main"] else "❌ pre-policy"
    dr = r["drawer"] or "—"
    note = "" if not r["ahead"] else f"oldest unmerged {r['oldest_unmerged']}"
    return (f"| `{r['name']}` | {gap} | {pol} | {len(r['claude'])} | `{dr}` | {note} |")


def render_md(realms: list[dict], decisions: list[dict], snap: dict | None,
              lanes: list[str], now: str) -> str:
    lines = [
        "# Hlidskjalf — the high seat",
        "",
        f"provenance: M · `python3 tools/hlidskjalf.py --write` · {now} · verify: re-run it —",
        "every figure regenerates from `git ls-remote` / `rev-list`, so nothing here depends on",
        "what any clone has fetched. PR rows are O-tier from docs/ai-cto/pr-snapshot.json and",
        "carry their capture time.",
        "",
        "**The seat sees; the hand stays the founder's.** This board is generated — edit the",
        "generator, `tools/hlidskjalf.py`, never this file. It ranks the decisions only the",
        "founder can make; it takes none of them.",
        "",
        "---",
        "",
        "## The decisions (ranked by what each unblocks — not alphabetical, deliberately)",
        "",
    ]
    for i, dec in enumerate(decisions, 1):
        lines += [
            f"### {i}. {dec['title']}",
            "",
            f"**Why now:** {dec['why']}",
            "",
            f"**The action, precisely:** {dec['action']}",
            "",
            f"**Unblocks:** {dec['unblocks']}",
            f"**Source:** {dec['source']}",
            "",
        ]
    lines += [
        "---",
        "",
        "## The realms (Z→A, house style)",
        "",
        "| Repo | Ygg vs main | policy on `main` | `claude/*` refs | drawer | note |",
        "| ---- | ----------- | ---------------- | --------------- | ------ | ---- |",
    ]
    lines += [fmt_realm_row(r) for r in realms]
    if snap:
        age = f"{snap['age_h']:.1f}h old" if snap.get("age_h") is not None else "age unknown"
        n_pr = sum(len(rp.get("open_prs", [])) for rp in snap.get("repos", {}).values())
        lines += ["", f"PR snapshot: **{n_pr} open PRs**, captured {snap.get('captured','?')} "
                      f"({age}) via {snap.get('via','?')}."]
    if lanes:
        lines += ["", "## Claimed lanes (norns.md §4, verbatim)", ""] + lanes
    lines += [
        "",
        "---",
        "",
        "Companion instruments: `tools/weave.py` (a Norn's next-move dispatcher) ·",
        "`docs/ai-cto/branch-retirement-manifest.md` (the deletion approval sheet) ·",
        "`tools/check-tiers.py` (the drawer-depth check the gate runs).",
        "",
    ]
    return "\n".join(lines)


def render_html(realms: list[dict], decisions: list[dict], snap: dict | None,
                now: str) -> str:
    e = html_mod.escape

    def dec_html(i: int, d: dict) -> str:
        return (f"<article><h3>{i}. {e(d['title'])}</h3>"
                f"<p><b>Why now</b> — {e(d['why'])}</p>"
                f"<p><b>The action</b> — {e(d['action'])}</p>"
                f"<p class='meta'><b>Unblocks:</b> {e(d['unblocks'])}<br>"
                f"<b>Source:</b> {e(d['source'])}</p></article>")

    rows = []
    for r in realms:
        if r.get("unreachable"):
            rows.append(f"<tr><td>{e(r['name'])}</td><td colspan='5'>remote unreachable</td></tr>")
            continue
        gap = f"+{r['ahead']}" + (f" / −{r['behind']}" if r["behind"] else "")
        pol = "yes" if r["policy_on_main"] else "NO — pre-policy"
        rows.append(f"<tr><td>{e(r['name'])}</td><td>{gap}</td><td>{pol}</td>"
                    f"<td>{len(r['claude'])}</td><td><code>{e(r['drawer'] or '—')}</code></td>"
                    f"<td>{e(r['oldest_unmerged'] or '')}</td></tr>")

    snap_line = ""
    if snap:
        n_pr = sum(len(rp.get("open_prs", [])) for rp in snap.get("repos", {}).values())
        age = f"{snap['age_h']:.1f}h" if snap.get("age_h") is not None else "?"
        snap_line = (f"<p class='meta'>PR snapshot: {n_pr} open PRs · captured "
                     f"{e(str(snap.get('captured','?')))} ({age} old). "
                     f"The ref list ages while you read it; so does this.</p>")

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hlidskjalf — the high seat</title>
<style>
  body{{font-family:{FONT};margin:0;background:#f7f5f0;color:#1c1a17;line-height:1.55}}
  header{{background:#1f2733;color:#f2ede2;padding:2.2rem 1.4rem 1.6rem}}
  header h1{{margin:0 0 .3rem;font-size:1.9rem;letter-spacing:.02em}}
  header p{{margin:.2rem 0;opacity:.85;max-width:60rem}}
  main{{max-width:60rem;margin:0 auto;padding:1.2rem 1.4rem 3rem}}
  h2{{border-bottom:2px solid #1f2733;padding-bottom:.25rem;margin-top:2.2rem}}
  article{{background:#fff;border:1px solid #d9d2c4;border-left:6px solid #8a5a1b;
          border-radius:6px;padding: .9rem 1.1rem;margin:1rem 0}}
  article h3{{margin:.1rem 0 .5rem}}
  .meta{{font-size:.9em;opacity:.8}}
  table{{border-collapse:collapse;width:100%;font-size:.95em}}
  th,td{{border:1px solid #d9d2c4;padding:.45rem .6rem;text-align:left}}
  th{{background:#ece7db}}
  code{{background:#ece7db;padding:.05rem .3rem;border-radius:3px}}
  footer{{max-width:60rem;margin:0 auto;padding:0 1.4rem 2rem;font-size:.85em;opacity:.75}}
</style></head><body>
<header>
  <h1>Hlidskjalf — the high seat</h1>
  <p>The seat sees; the hand stays the founder's. Generated {e(now)} by
  <code>tools/hlidskjalf.py</code> — the eye is in the well, and it takes no action.</p>
</header>
<main>
  <h2>The decisions — ranked by what each unblocks</h2>
  {''.join(dec_html(i, d) for i, d in enumerate(decisions, 1))}
  <h2>The realms (Z→A)</h2>
  <table><tr><th>Repo</th><th>Ygg vs main</th><th>policy on main</th>
  <th>claude/* refs</th><th>drawer</th><th>oldest unmerged</th></tr>
  {''.join(rows)}</table>
  {snap_line}
</main>
<footer>Provenance M for git figures (ls-remote / rev-list, re-measured each run) ·
O for PR rows (snapshot, capture time shown). Companion pages:
<a href="provenance.html">the Provenance Ladder</a> · <a href="bifrost.html">Bifrost</a> ·
<a href="edda.html">the Edda</a>.</footer>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true",
                    help="render docs/ai-cto/hlidskjalf-board.md + docs/hlidskjalf.html")
    ap.add_argument("--root", type=pathlib.Path, default=LOCALDNS.parent)
    args = ap.parse_args()

    if not args.root.is_dir():
        print(f"FATAL portfolio root unreadable: {args.root}", file=sys.stderr)
        return 2

    now = datetime.datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    realms = [survey(r) for r in discover(args.root)]
    snap = load_snapshot()
    lanes = load_lanes()
    decisions = decide(realms, snap)

    print(f"HLIDSKJALF · {now} · {len(realms)} realms in view\n")
    for i, d in enumerate(decisions, 1):
        print(f"  {i}. {d['title']}")
        print(f"     → {d['action'][:110]}{'…' if len(d['action']) > 110 else ''}")
    print()
    for r in realms:
        if r.get("unreachable"):
            print(f"  {r['name']:<46} UNREACHABLE")
            continue
        print(f"  {r['name']:<46} Ygg +{r['ahead']:<3} policy-on-main="
              f"{'yes' if r['policy_on_main'] else 'NO '} claude/*={len(r['claude'])}")

    if args.write:
        BOARD_MD.write_text(render_md(realms, decisions, snap, lanes, now), encoding="utf-8")
        BOARD_HTML.write_text(render_html(realms, decisions, snap, now), encoding="utf-8")
        print(f"\nwrote {BOARD_MD.relative_to(LOCALDNS)} and {BOARD_HTML.relative_to(LOCALDNS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
