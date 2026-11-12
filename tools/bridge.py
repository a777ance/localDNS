#!/usr/bin/env python3
"""bridge.py — the bridge display: the state of the loop as a text dashboard.

    python3 tools/bridge.py                 full screen. Tab or left/right change panel, 1-9 jump,
                                            up/down pick an item, Enter opens it, g runs the gates,
                                            i types a message to Claude (the console panel shows
                                            the reply), x stops Claude, ? shows the keys, q quits
    python3 tools/bridge.py --once [PANEL]  print one panel (or `all`) and exit; colour if a terminal
    python3 tools/bridge.py --plain [PANEL] the same with no colour codes, for pasting into a reply
    python3 tools/bridge.py --statusline    two lines for a status bar, from session facts on stdin
    python3 tools/bridge.py --check         draw every panel at several widths, with every item
                                            opened in turn; exit 1 on any fault

Panels: console, status, live, queue, decisions, activity, timing, branches, fleet, leans.

The console is Claude served through this display, not through Claude Code's own screen. A message
typed here is passed to `claude -p ... --output-format stream-json`, the documented way to run
Claude Code with no interface of its own, and each later message resumes the same conversation.
The repo's hooks run in that mode too, so the live panel fills as Claude works. Extra flags, such
as a permission mode, come from the environment variable BRIDGE_CLAUDE_ARGS; none is set here. Everything is read from
files and from git in this checkout; the display changes nothing. The look is in the spirit of the
"LCARS" panels the founder asked for: a block-colour side rail, pill labels, tiles, and bars.
Standard library only.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PANELS = ["console", "status", "live", "queue", "decisions", "activity", "timing", "branches", "fleet", "leans"]
ORANGE, PEACH, LAV, BLUE, RED, GREEN, GREY, WHITE = 208, 216, 141, 110, 203, 114, 245, 231
RAIL = [WHITE, ORANGE, GREEN, PEACH, LAV, BLUE, PEACH, LAV, BLUE, ORANGE]
LETTER = {"observe": "O", "orient": "OO", "decide": "D", "act": "A"}
CONSOLE = {"log": [], "proc": None, "buf": b"", "session": None, "cost": 0.0, "typing": None}
CANON = ["main", "leader", "outer", "main-before-evacuation"]
COLOR = True
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def fg(n, s):
    return f"\x1b[38;5;{n}m{s}\x1b[0m" if COLOR else s


def bg(n, s):
    return f"\x1b[48;5;{n}m\x1b[38;5;16m{s}\x1b[0m" if COLOR else s


def bold(s):
    return f"\x1b[1m{s}\x1b[0m" if COLOR else s


def vis(s):
    return len(ANSI.sub("", s))


def fit(s, width):
    """Pad or cut a line (which may hold colour codes) to exactly `width` visible columns."""
    if vis(s) <= width:
        return s + " " * (width - vis(s))
    out, seen, i = "", 0, 0
    while i < len(s) and seen < width - 1:
        m = ANSI.match(s, i)
        if m:
            out += m.group(0)
            i = m.end()
        else:
            out += s[i]
            seen += 1
            i += 1
    return out + ("\x1b[0m" if COLOR else "") + "…"


def bar(value, top, width, color=ORANGE):
    """A horizontal bar with eighth-block precision."""
    if top <= 0 or width <= 0:
        return ""
    cells = max(0.0, min(1.0, value / top)) * width
    full, part = int(cells), int((cells - int(cells)) * 8)
    body = "█" * full + (" ▏▎▍▌▋▊▉"[part] if part and full < width else "")
    return fg(color, body) + fg(GREY, "·" * (width - len(body)))


def spark(values):
    if not values:
        return ""
    top = max(values) or 1
    return "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v / top * 8 + 0.5))] for v in values)


def columns(values, height, color=ORANGE):
    """A vertical bar chart: `height` rows of text, one column per value, tallest value fills it."""
    top = max(values) if values and max(values) > 0 else 1
    rows = []
    for level in range(height, 0, -1):
        row = ""
        for v in values:
            eighths = v / top * height * 8 - (level - 1) * 8
            row += "█" if eighths >= 8 else " ▁▂▃▄▅▆▇"[int(eighths)] if eighths > 0 else " "
        rows.append(fg(color, row))
    return rows


def pill(color, text):
    return bg(color, f" {text} ")


def head(text, color=PEACH):
    return [pill(color, text.upper()), ""]


def item(line, detail):
    """A line the reader can pick with the arrows and open with Enter."""
    return {"t": line, "d": [d for d in detail if d is not None]}


def read(rel):
    f = ROOT / rel
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


_GIT = {}


def git(*args):
    """Ask git, remembering each answer for five seconds: one screen asks the same thing many times."""
    hit = _GIT.get(args)
    if hit and time.time() - hit[0] < 5:
        return hit[1]
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, timeout=5).stdout.strip()
    except Exception:
        out = ""
    _GIT[args] = (time.time(), out)
    return out


# ---- data, read fresh on every draw -------------------------------------------------------------

def queue_items():
    out = []
    for m in re.finditer(r"^- \*\*(SQ-(\d)\d\d) · (.*?)\*\*(.*)$", read("docs/ai-cto/superqueue.md"), re.MULTILINE):
        title, rest = m.group(3), m.group(4).strip()
        state = "done" if "DONE" in rest or "DONE" in title else "blocked" if "BLOCKED" in title else "open"
        title = re.sub(r"^BLOCKED on [^·]*· ", "", title).rstrip(".")
        out.append({"id": m.group(1), "lane": {"0": "loop", "1": "you"}.get(m.group(2), "later"),
                    "title": title, "state": state, "text": rest})
    return out


def decisions():
    out, text = [], read("docs/ai-cto/blocked.md")
    for m in re.finditer(r"^- \*\*(DEC-\d{3}) · (.*?) · (OPEN|GO|NO GO|MOOT)\b(.*(?:\n  .*)*)", text, re.MULTILINE):
        body = " ".join(m.group(4).replace("**", "").split()).lstrip(". ")
        out.append({"id": m.group(1), "title": m.group(2), "status": m.group(3), "text": body})
    return out


def timings():
    rows = []
    for line in read(".claude/.matrix-times").splitlines():
        p = line.split("\t")
        if len(p) == 4:
            try:
                rows.append((p[2].split(".")[0], float(p[3]), p[1]))
            except ValueError:
                pass
    return rows


def fleet():
    try:
        return json.loads(read(".claude/superfleet.json"))["scenarios"]
    except Exception:
        return []


def leans():
    out, tier, cur = [], "", None
    for line in read("docs/ai-cto/leans-e2e.md").splitlines():
        t = re.match(r"^## (Tier \d) · (.*)$", line)
        if t:
            tier, cur = f"{t.group(1)} · {t.group(2)}", None
            continue
        m = re.match(r"^(\d+)\. \*\*(.*?) \[(you|loop|both)\]\*\*(.*)$", line)
        if m:
            cur = {"n": int(m.group(1)), "title": m.group(2).rstrip("."), "who": m.group(3), "tier": tier, "text": m.group(4).strip()}
            out.append(cur)
        elif cur and line.startswith("   "):
            cur["text"] += " " + line.strip()
        elif line.startswith("## "):
            cur = None
    return out


GATES = {"at": None, "rows": []}


def run_gates():
    rows = []
    for check in sorted((ROOT / "tools").glob("check-*.py")):
        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, str(check)], capture_output=True, text=True, cwd=ROOT, timeout=60)
            ok, last = r.returncode == 0, ((r.stdout + r.stderr).strip().splitlines() or [""])[-1]
        except Exception as e:
            ok, last = False, str(e)
        rows.append((check.name, ok, time.time() - t0, last))
    GATES["at"], GATES["rows"] = time.strftime("%H:%M:%SZ", time.gmtime()), rows


# ---- panels: each returns a list of lines; a line is a string or an item() ---------------------

def panel_status(w):
    q, d, t = queue_items(), decisions(), timings()
    loop = [i for i in q if i["lane"] == "loop"]
    you = [i for i in q if i["lane"] == "you"]
    opens = [x for x in d if x["status"] == "OPEN"]
    mode = (re.search(r'"mode": "(\w+)"', read(".claude/cardinal-map.json")) or [None, "?"])[1]
    dirty = len(git("status", "--short").splitlines())
    over = sum(1 for r in t if r[1] > 10)
    todo_loop = sum(i["state"] != "done" for i in loop)
    todo_you = sum(i["state"] != "done" for i in you)
    k = lambda label: fg(GREY, f"{label:<14}")
    tiles = "  ".join([pill(ORANGE if opens else GREEN, f"{len(opens)} OPEN DECISIONS"), pill(PEACH, f"{todo_loop} FOR THE LOOP"),
                       pill(LAV, f"{todo_you} FOR YOU"), pill(RED if over else GREEN, f"{over} SLOW CALLS")])
    lines = head("status") + [tiles, "",
        k("branch") + bold(git("branch", "--show-current") or "(none)") + fg(GREY, "  at ") + git("log", "--format=%h", "-1"),
        k("gate mode") + fg(GREEN if mode == "warn" else ORANGE, mode) + fg(GREY, "   (labels and reminders; nothing is blocked)" if mode != "enforce" else ""),
        k("working tree") + (fg(GREEN, "clean") if not dirty else fg(RED, f"{dirty} file(s) not shipped")),
        "",
        k("loop's lane") + bar(len(loop) - todo_loop, len(loop) or 1, 24, GREEN) + f"  {len(loop) - todo_loop} of {len(loop)} done",
        k("your lane") + bar(len(you) - todo_you, len(you) or 1, 24, LAV) + f"  {len(you) - todo_you} of {len(you)} done",
        k("tool calls") + (f"{len(t)} timed  " + fg(ORANGE, spark([r[1] for r in t[-40:]])) if t else fg(GREY, "none timed on this machine")),
        ""]
    nxt = next((i for i in loop if i["state"] == "open"), None)
    lines.append(item(k("next for loop") + (fg(WHITE, f"{nxt['id']} · {nxt['title']}") if nxt else fg(GREEN, "nothing open")), [nxt["text"]] if nxt else []))
    nxt = next((i for i in you if i["state"] == "blocked"), None)
    lines.append(item(k("next for you") + (fg(WHITE, f"{nxt['id']} · {nxt['title']}") if nxt else fg(GREEN, "nothing waiting")), [nxt["text"]] if nxt else []))
    lines += ["", pill(BLUE, "GATES") + ("  " + fg(GREY, "not run in this display; press g") if not GATES["rows"] else fg(GREY, f"  run at {GATES['at']}"))]
    for name, ok, took, last in GATES["rows"]:
        lines.append(item(f"  {fg(GREEN, '●') if ok else fg(RED, '✖')} {name:<26}" + bar(took, 10, 16, GREEN if took < 10 else RED) + fg(GREY, f" {took:4.1f}s"), [last]))
    return lines


# ---- the console: Claude, served through this display ------------------------------------------

def say(kind, text):
    CONSOLE["log"].append((kind, text))
    del CONSOLE["log"][:-400]


def console_send(prompt):
    """Start one turn. Returns at once; console_pump() reads the reply as it arrives."""
    if CONSOLE["proc"] is not None:
        say("note", "Claude is still working. Press x to stop it first.")
        return
    say("you", prompt)
    cmd = [os.environ.get("BRIDGE_CLAUDE_BIN", "claude"), "-p", prompt, "--output-format", "stream-json", "--verbose"]
    if CONSOLE["session"]:
        cmd += ["--resume", CONSOLE["session"]]
    cmd += shlex.split(os.environ.get("BRIDGE_CLAUDE_ARGS", ""))
    try:
        CONSOLE["proc"] = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        CONSOLE["buf"] = b""
    except OSError as e:
        say("fail", f"Could not start Claude: {e}. Is the `claude` command installed and on the PATH?")


def console_line(raw):
    try:
        ev = json.loads(raw)
    except ValueError:
        if raw.strip():
            line = raw.strip()
            # A line Claude prints outside its stream is usually a warning. Show all of it, and
            # loudly if it is about safety: the first live run cut a sandbox warning off in grey.
            loud = line.startswith(("⚠", "Warning", "WARNING", "Error")) or "WITHOUT sandboxing" in line or "NOT be enforced" in line
            say("warn" if loud else "note", line[:2000])
        return
    kind = ev.get("type")
    if kind == "assistant":
        for block in (ev.get("message") or {}).get("content") or []:
            if block.get("type") == "text" and block.get("text", "").strip():
                say("claude", block["text"].strip())
            elif block.get("type") == "tool_use":
                inp = block.get("input") or {}
                what = inp.get("description") or inp.get("file_path") or inp.get("pattern") or inp.get("command") or ""
                say("tool", f"{block.get('name', '?')}  {str(what)[:120]}")
    elif kind == "system" and ev.get("subtype") == "init":
        CONSOLE["session"] = ev.get("session_id") or CONSOLE["session"]
    elif kind == "system" and ev.get("subtype") == "permission_denied":
        say("fail", "A step needed permission and nobody could give it. Set BRIDGE_CLAUDE_ARGS, for example to a permission mode, and restart the display.")
    elif kind == "result":
        CONSOLE["session"] = ev.get("session_id") or CONSOLE["session"]
        CONSOLE["cost"] = ev.get("total_cost_usd") or CONSOLE["cost"]
        if ev.get("is_error"):
            say("fail", str(ev.get("result") or "The turn ended with an error.")[:400])
        say("done", f"turn finished · conversation cost so far ${CONSOLE['cost']:.2f}")


def console_pump(wait=0.0):
    """Read whatever Claude has written. Returns True while a turn is still running."""
    import select
    proc = CONSOLE["proc"]
    if proc is None:
        return False
    while select.select([proc.stdout], [], [], wait)[0]:
        chunk = os.read(proc.stdout.fileno(), 65536)
        if not chunk:
            break
        CONSOLE["buf"] += chunk
        *lines, CONSOLE["buf"] = CONSOLE["buf"].split(b"\n")
        for line in lines:
            console_line(line.decode(errors="replace"))
        wait = 0.0
    if proc.poll() is not None:
        rest = proc.stdout.read() or b""
        for line in (CONSOLE["buf"] + rest).split(b"\n"):
            console_line(line.decode(errors="replace"))
        if proc.returncode not in (0, None) and not any(k == "done" for k, _ in CONSOLE["log"][-3:]):
            say("fail", f"Claude stopped with exit code {proc.returncode}.")
        CONSOLE["proc"], CONSOLE["buf"] = None, b""
        return False
    return True


def console_stop():
    proc = CONSOLE["proc"]
    if proc is not None:
        proc.terminate()
        say("note", "Stopped at your request. The unfinished turn was left as it was.")


def panel_console(w):
    lines = head("console", WHITE)
    busy = CONSOLE["proc"] is not None
    lines[0] += "  " + (pill(GREEN, "CLAUDE IS WORKING") if busy else fg(GREY, "press i to write to Claude")) + (fg(GREY, f"   ${CONSOLE['cost']:.2f} so far") if CONSOLE["cost"] else "")
    if not CONSOLE["log"]:
        lines += [fg(GREY, "This is Claude, served through this display. Press i, type a message, and press Enter."),
                  fg(GREY, "The reply appears here. The live panel (3) shows each step Claude takes, by letter."),
                  fg(GREY, "Each message continues the same conversation until you quit.")]
    style = {"you": (ORANGE, "YOU   "), "claude": (WHITE, "CLAUDE"), "tool": (BLUE, "  step"), "note": (GREY, "  note"),
             "fail": (RED, "FAILED"), "done": (GREEN, "  done"), "warn": (RED, "WARNING")}
    for kind, text in CONSOLE["log"]:
        color, label = style[kind]
        first = True
        for para in text.split("\n"):
            for wrapped in textwrap.wrap(para, max(20, w - 12)) or [""]:
                shown = fg(color, wrapped) if kind != "claude" else re.sub(r"\*\*(.+?)\*\*", lambda m: bold(m.group(1)), wrapped)
                lines.append((fg(color, label) if first else "      ") + "  " + shown)
                first = False
        if kind in ("claude", "done", "fail", "warn"):
            lines.append("")
    return lines


def panel_live(w):
    """What a Claude session in this checkout is doing: calls in flight, then the latest finished."""
    lines = head("live", GREEN)
    now = time.time()
    flying = []
    for f in sorted((ROOT / ".claude/.matrix-starts").glob("*")):
        try:
            started, alias = f.read_text(encoding="utf-8").split("\t", 1)
            flying.append((now - float(started), alias.strip()))
        except (OSError, ValueError):
            pass
    flying = [x for x in flying if x[0] < 600]
    lines.append(pill(GREEN if flying else GREY, f"{len(flying)} IN FLIGHT"))
    for age, alias in flying:
        letter = LETTER.get(alias.split(".")[0], "?")
        lines.append(f"  {fg(ORANGE, letter)}{' ' * (3 - len(letter))}{alias:<20} " + bar(age, 10, 20, RED if age > 10 else GREEN) + fg(GREY, f" {age:4.1f}s so far"))
    rows = [l.split("\t") for l in read(".claude/.matrix-times").splitlines()[-200:]]
    rows = [r for r in rows if len(r) == 4]
    lines += ["", pill(BLUE, "LATEST CALLS, NEWEST FIRST")]
    if not rows:
        lines.append(fg(GREY, "  No calls recorded on this machine. Write to Claude from the console and this fills as it works."))
    for when, tool, alias, secs in reversed(rows[-18:]):
        letter, s = LETTER.get(alias.split(".")[0], "?"), float(secs)
        lines.append(f"  {fg(GREY, when[11:19])}  {fg(ORANGE, letter)}{' ' * (3 - len(letter))}{alias:<18} " + bar(s, 10, 14, RED if s > 10 else GREEN) + fg(GREY, f" {s:5.1f}s  ") + tool[:28])
    trail = " ".join(LETTER.get(r[2].split(".")[0], "?") for r in rows[-40:])
    if trail:
        lines += ["", fg(GREY, "the trail  ") + fg(ORANGE, trail)]
    return lines


def statusline():
    """Two lines for a status bar. Fast, and quiet on any fault: a status bar must never break."""
    try:
        data = json.loads(sys.stdin.read() or "{}") if not sys.stdin.isatty() else {}
    except ValueError:
        data = {}
    q, d = queue_items(), decisions()
    opens = [x for x in d if x["status"] == "OPEN"]
    nxt = next((i for i in q if i["lane"] == "loop" and i["state"] == "open"), None)
    mode = (re.search(r'"mode": "(\w+)"', read(".claude/cardinal-map.json")) or [None, "?"])[1]
    rows = [l.split("\t") for l in read(".claude/.matrix-times").splitlines()[-40:]]
    rows = [r for r in rows if len(r) == 4]
    trail = "".join(LETTER.get(r[2].split(".")[0], "?")[0] for r in rows[-16:])
    slow = sum(1 for r in rows if float(r[3]) > 10)
    pct = ((data.get("context_window") or {}).get("used_percentage")) or 0
    cost = ((data.get("cost") or {}).get("total_cost_usd")) or 0
    print(" ".join([pill(ORANGE, "LOCALDNS"), bold(git("branch", "--show-current") or "?"), fg(GREY, mode),
                    pill(ORANGE if opens else GREEN, f"{len(opens)} OPEN"),
                    fg(WHITE, f"next {nxt['id']} {nxt['title'][:44]}") if nxt else fg(GREEN, "queue clear")]))
    print(" ".join(x for x in [fg(GREY, "context"), bar(pct, 100, 16, RED if pct > 80 else GREEN), f"{pct:.0f}%",
                               fg(GREY, " cost"), f"${cost:.2f}", fg(GREY, " trail"), fg(ORANGE, trail or "-"),
                               pill(RED, f"{slow} SLOW") if slow else ""] if x))


def panel_queue(w):
    q = queue_items()
    lines = head("superqueue")
    marks = {"done": fg(GREEN, "✔"), "open": fg(ORANGE, "●"), "blocked": fg(GREY, "○")}
    for lane, label, color in (("loop", "THE LOOP'S LANE", ORANGE), ("you", "YOUR LANE", LAV), ("later", "AFTER YOUR LANE MOVES", BLUE)):
        items = [i for i in q if i["lane"] == lane]
        done = sum(i["state"] == "done" for i in items)
        lines.append(pill(color, label) + "  " + bar(done, len(items) or 1, 20, color) + fg(GREY, f"  {done}/{len(items)}"))
        for i in items:
            lines.append(item(f"  {marks[i['state']]} {fg(GREY, i['id'])}  {i['title']}", [i["text"]]))
        lines.append("")
    lines.append(fg(GREY, "✔ done   ● open, a session can take it   ○ waiting on you or on an earlier item"))
    return lines


def panel_decisions(w):
    d = decisions()
    lines = head("decisions")
    counts = {}
    for x in d:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    colors = {"OPEN": ORANGE, "GO": GREEN, "NO GO": RED, "MOOT": GREY}
    for status in ("OPEN", "GO", "NO GO", "MOOT"):
        n = counts.get(status, 0)
        lines.append(f"  {status:<6} " + bar(n, max(counts.values() or [1]), 28, colors[status]) + f"  {n}")
    lines += ["", pill(ORANGE, "OPEN, NEWEST FIRST")]
    for x in [x for x in d if x["status"] == "OPEN"]:
        lines.append(item(f"  {fg(ORANGE, x['id'])}  {x['title']}", [x["text"]]))
    lines += ["", pill(GREEN, "DECIDED, NEWEST FIRST")]
    for x in [x for x in d if x["status"] != "OPEN"]:
        lines.append(item(f"  {fg(GREY, x['id'])}  {fg(colors[x['status']], x['status'])}{' ' * (5 - len(x['status']))}  {x['title']}", [x["text"]]))
    return lines


def panel_activity(w):
    lines = head("activity")
    now = int(time.time())
    stamps = [int(s) for s in git("log", "--since=24 hours ago", "--format=%ct").split() if s.isdigit()]
    hours = [0] * 24
    for s in stamps:
        age = (now - s) // 3600
        if 0 <= age < 24:
            hours[23 - age] += 1
    if not stamps:
        lines.append(fg(GREY, "No commits on this branch in the last 24 hours."))
    else:
        top = max(hours)
        chart = columns([h for h in hours for _ in (0, 1)], 6, ORANGE)
        for i, row in enumerate(chart):
            lines.append(fg(GREY, f"{top if i == 0 else '':>4} ") + row)
        lines.append(fg(GREY, "   0 " + "─" * 48))
        lines.append(fg(GREY, "     24 h ago" + " " * 12 + "12 h ago" + " " * 17 + "now"))
        lines += ["", pill(ORANGE, f"{len(stamps)} COMMITS IN 24 HOURS") + fg(GREY, f"   busiest hour: {top}")]
    lines += ["", pill(BLUE, "LATEST")]
    for row in git("log", "-12", "--format=%h\t%cr\t%s").splitlines():
        p = row.split("\t")
        if len(p) == 3:
            lines.append(item(f"  {fg(ORANGE, p[0])}  {fg(GREY, f'{p[1]:<15}')} {p[2]}",
                              git("show", "--stat", "--format=", p[0]).splitlines()[-8:]))
    return lines


def panel_timing(w):
    t = timings()
    lines = head("tool timing")
    if not t:
        return lines + [fg(GREY, "No tool calls have been timed on this machine."),
                        fg(GREY, "The stopwatch runs inside a Claude session in this checkout; its log is not in git.")]
    by = {}
    for card, secs, _tool in t:
        by.setdefault(card, []).append(secs)
    scale = max(max(max(v) for v in by.values()), 10.0)
    width = max(10, min(40, w - 44))
    cap = int(10 / scale * width)
    lines.append(fg(GREY, f"{'':<10}{'calls':>5}  median  worst   0 s") + " " * max(0, cap - 3) + fg(RED, "│10 s cap"))
    for card in ("observe", "orient", "decide", "act"):
        v = sorted(by.get(card, []))
        if v:
            lines.append(bold(card) + " " * (10 - len(card)) + f"{len(v):>5}  {v[len(v) // 2]:5.2f}s {v[-1]:5.1f}s   " + bar(v[-1], scale, width, RED if v[-1] > 10 else GREEN))
    over = [r for r in t if r[1] > 10]
    lines += ["", fg(GREY, "last 60 calls  ") + fg(ORANGE, spark([r[1] for r in t[-60:]])), "",
              pill(RED if over else GREEN, f"{len(over)} OF {len(t)} CALLS OVER 10 S")]
    for card, secs, tool in sorted(over, key=lambda r: -r[1])[:8]:
        lines.append(f"  {fg(RED, f'{secs:5.1f}s')}  {card:<8} {tool}")
    return lines


def panel_branches(w):
    lines = head("branches")
    refs = [r for r in git("for-each-ref", "refs/remotes/origin", "--format=%(refname:short)\t%(objectname:short)\t%(committerdate:relative)").splitlines() if "\t" in r]
    seen = {r.split("\t")[0].replace("origin/", "", 1): r.split("\t")[1:] for r in refs}
    role = {"main": "intent cold storage", "leader": "where all work lands", "outer": "home for non-OODA files",
            "main-before-evacuation": "the undo copy"}
    lines.append(pill(ORANGE, "THE CANONICAL BRANCHES"))
    for name in CANON:
        if name not in seen:
            lines.append(f"  {fg(RED, '✖')} {name:<24}" + fg(GREY, "not fetched on this machine"))
            continue
        lr = git("rev-list", "--left-right", "--count", f"origin/leader...origin/{name}").split()
        behind, ahead = (lr + ["?", "?"])[:2]
        files = len(git("ls-tree", "-r", "--name-only", f"origin/{name}").splitlines())
        lines.append(item(f"  {fg(GREEN, '●')} {bold(name)}{' ' * (24 - len(name))}{fg(ORANGE, seen[name][0])}  {fg(GREY, role[name])}",
                          [f"{files} files. Compared with leader: {ahead} commit(s) of its own, {behind} behind. Last commit {seen[name][1]}."]))
    extra = sorted((n for n in seen if n not in CANON and n != "HEAD"), reverse=True)
    lines += ["", pill(GREY, f"{len(extra)} OTHER BRANCHES") + fg(GREY, "   marked superfluous in docs/ai-cto/branches.md")]
    for name in extra:
        own = git("rev-list", "--count", f"origin/leader..origin/{name}") or "?"
        mark = fg(GREY, "○") if own == "0" else fg(ORANGE, "●")
        age = seen[name][1]
        lines.append(f"  {mark} {name:<40} {fg(GREY, age)}{' ' * max(1, 16 - len(age))}" + (fg(GREY, "nothing leader lacks") if own == "0" else fg(ORANGE, f"{own} commit(s) of its own")))
    return lines


def panel_fleet(w):
    f = fleet()
    lines = head("superfleet")
    if not f:
        return lines + [fg(GREY, "No fleet plan in this checkout.")]
    top = max(len(s["lanes"]) for s in f)
    for s in f:
        detail = [s["goal"], f"Look first: {s['look_first']}"] + [f"{l['id']} · {l['covers']}. Done when: {l['done_when']}." for l in s["lanes"]] + [f"Review: {s['review']}"]
        lines.append(item(f"{fg(ORANGE, s['id'])}  " + bar(len(s["lanes"]), top, 8, LAV) + f" {len(s['lanes'])}  {s['title']}", detail))
    lines += ["", pill(LAV, f"{len(f)} SCENARIOS · {sum(len(s['lanes']) for s in f)} LANES") + fg(GREY, "   no lane has run")]
    return lines


def panel_leans(w):
    ls = leans()
    lines = head("thirty leans")
    if not ls:
        return lines + [fg(GREY, "No leans file in this checkout.")]
    who = {"you": 0, "loop": 0, "both": 0}
    for x in ls:
        who[x["who"]] += 1
    colors = {"you": LAV, "loop": ORANGE, "both": BLUE}
    for k in ("you", "loop", "both"):
        lines.append(f"  {k:<5} " + bar(who[k], len(ls), 30, colors[k]) + f"  {who[k]}")
    tier = None
    for x in ls:
        if x["tier"] != tier:
            tier = x["tier"]
            lines += ["", pill(PEACH, tier.upper())]
        lines.append(item(f"  {x['n']:>2}  {fg(colors[x['who']], x['who'])}{' ' * (4 - len(x['who']))}  {x['title']}", [x["text"]]))
    return lines


def panel_help(w):
    rows = [("Tab  →", "next panel"), ("Shift-Tab  ←", "previous panel"), ("1 to 9, 0", "jump to a panel (0 is the tenth)"), ("i", "write a message to Claude; Enter sends it, Esc cancels"),
            ("x", "stop Claude mid-turn"),
            ("↑  ↓", "pick an item (marked ▸); on a panel with none, scroll"), ("Enter", "open or close the picked item"),
            ("PgUp  PgDn  Space", "scroll a page"), ("g", "run all the gates and show each with its time"),
            ("r", "redraw now (it also redraws twice a minute)"), ("?", "this screen"), ("q", "quit")]
    return head("keys") + [f"  {fg(ORANGE, f'{k:<20}')} {v}" for k, v in rows] + [
        "", fg(GREY, "Everything here is read from files and from git in this checkout. The display changes nothing;"),
        fg(GREY, "the one thing it runs is the gates, when you press g.")]


DRAW = {"console": panel_console, "status": panel_status, "live": panel_live, "queue": panel_queue, "decisions": panel_decisions, "activity": panel_activity,
        "timing": panel_timing, "branches": panel_branches, "fleet": panel_fleet, "leans": panel_leans, "help": panel_help}


def layout(panel, body_w, sel=None, opened=False):
    """Flatten a panel into text lines. Returns (lines, row of the picked item, number of items)."""
    out, pick_row, n = [], None, 0
    for entry in DRAW[panel](body_w):
        if isinstance(entry, str):
            out.append(entry)
            continue
        picked = sel is not None and n == sel
        if picked:
            pick_row = len(out)
            out.append(fg(WHITE, "▸") + entry["t"][1:] if entry["t"].startswith(" ") else fg(WHITE, "▸ ") + entry["t"])
            if opened:
                for para in entry["d"] or ["(nothing more is recorded for this item)"]:
                    for wrapped in textwrap.wrap(para, max(20, body_w - 8)) or [""]:
                        out.append("    " + fg(PEACH, "│ ") + wrapped)
        else:
            out.append(entry["t"])
        n += 1
    return out, pick_row, n


def frame(panel, w, h=None, scroll=0, sel=None, opened=False):
    """The whole screen: top bar, side rail, the panel's body, bottom bar. Returns (lines, scroll, items)."""
    rail_w = 14
    body, pick_row, n = layout(panel, w - rail_w - 2, sel, opened)
    more = 0
    if h:
        room = h - 4
        if pick_row is not None:
            scroll = min(scroll, pick_row)
            if pick_row >= scroll + room:
                scroll = pick_row - room + 1
        scroll = max(0, min(scroll, max(0, len(body) - room)))
        more = len(body) - room - scroll
        body = body[scroll:scroll + room]
        body += [""] * max(0, room - len(body))
    clock = time.strftime("%H:%MZ", time.gmtime())
    title = fg(ORANGE, "◢") + bg(ORANGE, " LOCALDNS BRIDGE ".ljust(rail_w)) + " " + bg(PEACH, f" {panel.upper()} ")
    out = [fit(title + " " + fg(ORANGE, "━" * max(0, w - vis(title) - 10)) + " " + bg(LAV, f" {clock} "), w), ""]
    for row, line in enumerate(body):
        slot, sub = divmod(row, 2)
        if slot < len(PANELS):
            name = PANELS[slot]
            label = f"{slot + 1:>2} {name.upper():<10}" if sub == 0 else ""
            cell = bg(WHITE if name == panel else RAIL[slot], label.ljust(rail_w - 1)) + (fg(WHITE, "▌") if name == panel else " ")
        else:
            cell = (bg(GREY if (row // 2) % 3 else ORANGE, " " * (rail_w - 1)) + " ") if h else " " * rail_w
        out.append(fit(cell + " " + line, w))
    if h and CONSOLE["typing"] is not None:
        typed = CONSOLE["typing"][-(w - 24):]
        out += ["", fit(bg(WHITE, " TO CLAUDE ") + " " + typed + fg(ORANGE, "█") + fg(GREY, "   Enter sends · Esc cancels"), w)]
    elif h:
        keys = " Tab panel · i write to Claude · ↑↓ pick · Enter open · ? keys · q quit "
        foot = fg(ORANGE, "◥") + bg(ORANGE, keys) + " " + fg(ORANGE, "━" * max(0, w - len(keys) - 16)) + (" " + bg(PEACH, f" +{more} more ") if more > 0 else "")
        out += ["", fit(foot, w)]
    return out, scroll, n


def interactive():
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    idx, scroll, sel, opened, helping = 0, 0, None, False, False
    sys.stdout.write("\x1b[?1049h\x1b[?25l")
    try:
        tty.setcbreak(fd)
        while True:
            w, h = shutil.get_terminal_size((100, 30))
            lines, scroll, n = frame("help" if helping else PANELS[idx], w, h, scroll, sel, opened)
            sys.stdout.write("\x1b[H\x1b[2J" + "\n".join(lines))
            sys.stdout.flush()
            busy = CONSOLE["proc"] is not None
            if not select.select([sys.stdin], [], [], 0.3 if busy else 30)[0]:
                before = len(CONSOLE["log"])
                console_pump()
                if PANELS[idx] == "console" and len(CONSOLE["log"]) != before:
                    scroll = 10 ** 9  # follow the reply as it arrives
                continue  # no key: redraw, so the clock, the files and the reply stay current
            ch = os.read(fd, 64).decode(errors="ignore")
            if CONSOLE["typing"] is not None:
                if ch in ("\r", "\n"):
                    text, CONSOLE["typing"] = CONSOLE["typing"].strip(), None
                    if text:
                        console_send(text)
                        scroll = 10 ** 9
                elif ch == "\x1b":
                    CONSOLE["typing"] = None
                elif ch in ("\x7f", "\x08"):
                    CONSOLE["typing"] = CONSOLE["typing"][:-1]
                elif ch == "\x15":
                    CONSOLE["typing"] = ""
                elif not ch.startswith("\x1b"):
                    CONSOLE["typing"] += "".join(c for c in ch if c.isprintable())
                continue
            if ch in ("q", "Q", "\x03"):
                console_stop()
                break
            if helping:
                helping, scroll = False, 0
                continue
            go = None
            if ch in ("\t", "\x1b[C"):
                go = (idx + 1) % len(PANELS)
            elif ch in ("\x1b[Z", "\x1b[D"):
                go = (idx - 1) % len(PANELS)
            elif ch.isdigit() and (int(ch) or 10) <= len(PANELS):
                go = (int(ch) or 10) - 1
            elif ch in ("i", "I"):
                idx, sel, opened, scroll = PANELS.index("console"), None, False, 10 ** 9
                CONSOLE["typing"] = ""
            elif ch in ("x", "X"):
                console_stop()
            elif ch in ("\x1b[B", "j"):
                if n:
                    sel, opened = (0 if sel is None else min(n - 1, sel + 1)), False
                else:
                    scroll += 1
            elif ch in ("\x1b[A", "k"):
                if n and sel is not None:
                    sel, opened = max(0, sel - 1), False
                else:
                    scroll = max(0, scroll - 1)
            elif ch in ("\r", "\n") and sel is not None:
                opened = not opened
            elif ch in ("\x1b[6~", " "):
                scroll, sel = scroll + max(1, h - 6), None
            elif ch == "\x1b[5~":
                scroll, sel = max(0, scroll - max(1, h - 6)), None
            elif ch == "?":
                helping, scroll = True, 0
            elif ch in ("g", "G"):
                sys.stdout.write("\x1b[H\x1b[2J  running the gates…")
                sys.stdout.flush()
                run_gates()
                go = 0
            if go is not None:
                idx, scroll, sel, opened = go, 0, None, False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


def check():
    global COLOR
    faults, drawn = [], 0
    for color in (True, False):
        COLOR = color
        for w in (60, 80, 103, 160):
            for panel in list(DRAW):
                for h in (None, 24):
                    try:
                        _lines, _s, n = frame(panel, w, h)
                        picks = [(None, False)] + ([(i, True) for i in range(n)] if (w == 103 and h) else [])
                        for sel, opened in picks:
                            lines, _s, _n = frame(panel, w, h, 0, sel, opened)
                            drawn += 1
                            if any(vis(l) > w for l in lines):
                                faults.append(f"{panel} at width {w}, item {sel}: a line is wider than the screen")
                            if h and len(lines) != h:
                                faults.append(f"{panel} at width {w}, item {sel}: {len(lines)} rows drawn on a {h}-row screen")
                            if not color and any("\x1b" in l for l in lines):
                                faults.append(f"{panel}: plain mode still holds colour codes")
                    except Exception as e:  # a panel must never take the display down
                        faults.append(f"{panel} at width {w}: {type(e).__name__}: {e}")
    faults += check_console()
    for f in sorted(set(faults)):
        print("FAIL", f)
    if not faults:
        print(f"ok   bridge display: {len(DRAW)} panels, {drawn} screens drawn at 4 widths, in colour and plain, every item opened")
    return 1 if faults else 0


def check_console():
    """Drive one console turn against a stand-in for the `claude` command that speaks stream-json."""
    import tempfile
    faults = []
    events = [{"type": "system", "subtype": "init", "session_id": "s-1"},
              {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "README.md"}}]}},
              {"type": "assistant", "message": {"content": [{"type": "text", "text": "**Done.** Read it."}]}},
              {"type": "result", "subtype": "success", "result": "ok", "session_id": "s-1", "total_cost_usd": 0.42}]
    with tempfile.TemporaryDirectory() as tmp:
        stub = Path(tmp) / "claude"
        stub.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$0.args\"\ncat <<'EOF'\n" + "\n".join(json.dumps(e) for e in events) + "\nnot json\n⚠ Sandbox disabled: commands will run WITHOUT sandboxing.\nEOF\n")
        stub.chmod(0o755)
        old = os.environ.get("BRIDGE_CLAUDE_BIN")
        os.environ["BRIDGE_CLAUDE_BIN"] = str(stub)
        try:
            for turn in (1, 2):
                console_send(f"hello {turn}")
                deadline = time.time() + 5
                while console_pump(0.2) and time.time() < deadline:
                    pass
                args = (Path(str(stub) + ".args").read_text() if Path(str(stub) + ".args").exists() else "").split("\n")
                if turn == 2 and "--resume" not in args:
                    faults.append("console: the second message did not resume the first conversation")
            kinds = [k for k, _ in CONSOLE["log"]]
            for want in ("you", "tool", "claude", "done", "note", "warn"):
                if want not in kinds:
                    faults.append(f"console: no {want!r} line after a turn")
            if CONSOLE["session"] != "s-1" or abs(CONSOLE["cost"] - 0.42) > 1e-9:
                faults.append("console: session id or cost not taken from the result line")
            if CONSOLE["proc"] is not None:
                faults.append("console: the turn did not finish")
            os.environ["BRIDGE_CLAUDE_BIN"] = str(Path(tmp) / "no-such-command")
            console_send("hello")
            if not any(k == "fail" for k, _ in CONSOLE["log"][-2:]):
                faults.append("console: a missing `claude` command must be reported, not raised")
            for w in (60, 103):
                lines, _s, _n = frame("console", w, 24, 10 ** 9)
                if any(vis(l) > w for l in lines) or len(lines) != 24:
                    faults.append(f"console: transcript does not fit a {w}-column screen")
        finally:
            if old is None:
                os.environ.pop("BRIDGE_CLAUDE_BIN", None)
            else:
                os.environ["BRIDGE_CLAUDE_BIN"] = old
            CONSOLE.update(log=[], proc=None, buf=b"", session=None, cost=0.0, typing=None)
    return faults


def main():
    global COLOR
    args = sys.argv[1:]
    if args[:1] == ["--check"]:
        return check()
    if args[:1] == ["--statusline"]:
        try:
            statusline()
        except Exception:
            print("localDNS")  # never leave a status bar broken
        return 0
    if args[:1] in (["--once"], ["--plain"]):
        COLOR = args[0] == "--once" and sys.stdout.isatty()
        want = args[1] if len(args) > 1 else "status"
        names = PANELS if want == "all" else [want]
        if any(n not in DRAW for n in names):
            print(f"FAILED: no panel {want!r}. Panels: {', '.join(PANELS)}, all")
            return 1
        w = min(shutil.get_terminal_size((100, 30)).columns, 120)
        for n in names:
            print("\n".join(l.rstrip() for l in frame(n, w)[0]))
            print()
        return 0
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        COLOR = False  # piped or redirected: plain text, never colour codes in a file
        print("\n".join(l.rstrip() for l in frame("status", 100)[0]))
        return 0
    interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
