#!/usr/bin/env python3
"""Stop hook — the Briefing reply rules that decide mechanically.

Checks the reply that is ending the turn and blocks the stop, with the reasons, if it
breaks one of these (the keys are what tools/check-stop-hook.py tests and what it
requires .claude/output-styles/briefing.md to name):

  LEAD     the reply opens with a bold state word
  ACT      a numbered Decide list is acted on: an Act section with at least as many lines
  CD       every fenced bash block starts with cd, and never with the cloud container's path
  HEDGE    no vague hedge outside code and quotes
  REHEARSE a bash block handed to the founder was run first (decide.rehearse), or says why not
  SCRATCH  every new file in the session's scratchpad is announced by its full path
  LANDING  the last line says where we landed on the N items: **Landed · N = <count>:** ...
  NEXT     a stop names the next action (uncommitted work, an open stall, the next queue item)
           unless the reply says why it stops, on a line starting "Stopping because:"
  TILE     a DECISION tile has both action lines, the GO / NO GO line, and a logged DEC id

Loop safety: when Claude Code re-enters the turn because of this hook, the
input carries stop_hook_active=true. This hook then allows the stop, so it
fires at most once per turn and cannot run away.

Reads the Stop hook JSON on stdin. Standard library only.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
HEDGES = ("should work", "probably works", "probably work", "may have worked", "might have worked", "should be fine")


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


def act_lines(text):
    """Count list lines in the Act section that follows the Decide list."""
    d = re.search(r"^\W*Decide[ds]?\b.*$", text, re.MULTILINE)
    m = re.search(r"^\W*Act(ed)?\b.*$", text[d.end():] if d else "", re.MULTILINE)
    if not m:
        return 0
    n = 0
    for line in text[d.end() + m.end():].splitlines():
        if re.match(r"^#{1,3}\s|^\*\*[A-Z]\w+\.?\*\*\.?\s*$", line):
            break  # the next section
        if re.match(r"^\s*(\d+\.|[-*])\s+\S", line):
            n += 1
    return n


def prose(text):
    """The reply without fenced blocks, inline code, or double-quoted spans."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"[\"\u201c][^\"\u201d\n]*[\"\u201d]", "", text)


def scratch_unannounced(text, session_id):
    """New top-level scratchpad entries this reply does not name by full path. Named ones are recorded."""
    import glob
    base = os.environ.get("MATRIX_SCRATCH_DIR")
    dirs = [base] if base else (glob.glob(f"/tmp/claude-*/*/{session_id}/scratchpad") if session_id else [])
    store = ROOT / ".claude/.matrix-scratch"
    known = set(store.read_text(encoding="utf-8").splitlines()) if store.exists() else set()
    new = sorted(str(f) for d in dirs for f in Path(d).glob("*") if str(f) not in known)
    named = [f for f in new if f in text]
    if named:
        with open(store, "a", encoding="utf-8") as fh:
            fh.write("".join(f + "\n" for f in named))
    return [f for f in new if f not in named]


def next_action():
    """What the loop should do next, read from disk. None when nothing is waiting."""
    import subprocess
    try:
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT,
                               timeout=3).stdout.strip().splitlines()
    except Exception:
        dirty = []
    if dirty:
        return ("%d file(s) are changed and not shipped (%s). Ship them: python3 tools/matrix.py act.ship "
                "\"MESSAGE\" FILE... --push" % (len(dirty), ", ".join(l.split()[-1] for l in dirty[:4])))
    if list((ROOT / ".claude/.matrix-stalls").glob("*.json")):
        return "a Matrix stall is open. Diagnose it: python3 tools/matrix.py orient.stall"
    try:
        queue = (ROOT / "docs/ai-cto/handoff.md").read_text(encoding="utf-8")
    except OSError:
        return None
    for m in re.finditer(r"^- \*\*(Q-\d{3}) · (.*?)\*\*.*$", queue, re.MULTILINE):
        if not re.search(r"BLOCKED|DONE|SKIPPED", m.group(0)):
            return "the next queue item is %s · %s (docs/ai-cto/handoff.md). Start it now." % (m.group(1), m.group(2)[:90])
    return None


def review(text, session_id=""):
    """Return the list of reasons this reply may not end the turn. Empty means allow."""
    reasons = []
    # SCRATCH. A scratchpad nobody was told about is lost in the woodwork.
    try:
        lost = scratch_unannounced(text, session_id)
    except Exception:
        lost = []
    if lost:
        reasons.append("SCRATCHPAD: %d scratchpad file(s) have not been announced. Name each by its full path and say "
                       "what it is, or delete it if it is not needed:\n%s" % (len(lost), "\n".join(lost[:8])))
    # LEAD. Punctuation may sit just inside or just after the bold (**Done.** / **Done**:).
    first = next((l for l in text.splitlines() if l.strip()), "")
    if not re.match(r"^\*\*(Done|Partial|Blocked|Waiting)[.:,]?\*\*[.:,]?(\s|$)", first.strip()):
        reasons.append(
            "BRIEFING LEAD: the reply must open with one bold state word (**Done**, **Partial**, "
            "**Blocked**, or **Waiting**). It opened with: %r. Restate the reply with the state word first."
            % first.strip()[:80])
    # ACT. A Decide list is a queue to run, not a menu: it needs as many Act lines as it has items.
    items = decide_items(text)
    acted = act_lines(text) if items else 0
    if items and acted < len(items):
        reasons.append(
            "OODA ACT: the Decide list has %d numbered item(s) and the Act section reports %d. Act on them "
            "now, in order, without choosing between them or asking first, and report one Act line per item "
            "(or say why that item is blocked). Skip only an item the user has marked punt. "
            "Irreversible or outward-facing actions still need a confirm first.\n\n%s"
            % (len(items), acted, "\n".join(items)))
    # CD. The founder opens a fresh terminal for every command.
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
        lines = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().startswith("#")]
        if lines and lines[0].startswith("cd /home/user/"):
            reasons.append("COMMAND CD: this bash block uses the cloud container's path (/home/user/...), which does "
                           "not exist on the founder's machine. Use: cd ~/localDNS")
            break
        if lines and not lines[0].startswith("cd "):
            reasons.append("COMMAND CD: every bash block must start with the cd to the repo. "
                           "This block starts with: %r" % lines[0][:80])
            break
    # REHEARSE. Look before the founder leaps: a command handed to him was run here first.
    if "Not rehearsed:" not in text:
        try:
            import hashlib
            done = {l.split("\t")[0] for l in (ROOT / ".claude/.matrix-rehearsed").read_text(encoding="utf-8").splitlines()
                    if l.split("\t")[1:2] == ["0"]}
        except OSError:
            done = set()
        for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
            lines = [l.strip() for l in block.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
            if lines and re.match(r"cd\s+\S+$", lines[0]):
                lines = lines[1:]
            elif lines:  # the one-line form: cd REPO && command
                lines[0] = re.sub(r"^cd\s+\S+\s*&&\s*", "", lines[0])
            body = "\n".join(lines)
            if body and hashlib.sha256(body.encode()).hexdigest() not in done:
                reasons.append(
                    "REHEARSE: this command is being handed to the founder without having been run: %r. Run it first "
                    "in a copy of his checkout: python3 tools/matrix.py decide.rehearse [--at REV] [--setup CMD] "
                    "\"COMMAND\" (it must exit 0). If it cannot be rehearsed here, say so in the reply on a line "
                    "starting 'Not rehearsed:' with the reason." % body[:100])
                break
    # HEDGE.
    low = prose(text).lower()
    found = [h for h in HEDGES if h in low]
    if found:
        reasons.append("NO HEDGE: the reply says %s. Replace it with the check that would confirm it, "
                       "or with what was verified." % ", ".join(repr(h) for h in found))
    # TILE.
    try:
        log = (ROOT / "docs/ai-cto/blocked.md").read_text(encoding="utf-8")
    except OSError:
        log = None
    for dec in dict.fromkeys(re.findall(r"DECISION · (DEC-\d{3})", text)):
        missing = [part for part in ("Action if GO:", "Action if NO GO:", "Decision needed:") if part not in text]
        if log is not None and ("**%s " % dec) not in log:
            missing.append("an entry for %s in docs/ai-cto/blocked.md" % dec)
        if missing:
            reasons.append("TILE: the tile for %s is missing: %s." % (dec, "; ".join(missing)))
    # NEXT. The founder's rule, 2026-11-12: the Stop hook starts the next action. A stop is allowed
    # only when nothing is waiting, or when the reply says why it stops.
    if "Stopping because:" not in text:
        try:
            todo = next_action()
        except Exception:
            todo = None
        if todo:
            reasons.append(
                "NEXT ACTION: do not stop here; %s If stopping is right (waiting on the founder, on an "
                "event, or the work was a question and not a task), say so on a line starting "
                "'Stopping because:' and end the reply." % todo)
    # LANDING. The founder's rule, 2026-11-12: the last sentence always answers "where did we land on N x".
    last = next((l for l in reversed(text.splitlines()) if l.strip()), "")
    if not re.match(r"^\*\*Landed · N = \d+:\*\*\s+\S", last.strip()):
        reasons.append(
            "LANDING: the reply must end with one line that says where we landed, in this form: "
            "**Landed · N = <count>:** then where each of the N items in play stands, in one sentence. "
            "It ended with: %r" % last.strip()[:80])
    return reasons


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail open: never trap the session on malformed input
    if data.get("stop_hook_active"):
        return 0  # already continued once this turn; let it end
    try:
        text = last_assistant_text(data.get("transcript_path", ""))
        reasons = review(text, str(data.get("session_id") or "")) if text.strip() else []
    except Exception:
        return 0  # fail open
    if not reasons:
        return 0
    print(json.dumps({"decision": "block", "reason": "\n\n".join(reasons)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
