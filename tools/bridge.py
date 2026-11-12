#!/usr/bin/env python3
"""bridge.py — the bridge display: the state of the loop as a text dashboard.

    python3 tools/bridge.py                 full screen; Tab or arrows change panel, 1-6 jump,
                                            g runs the gates, r refreshes, q quits
    python3 tools/bridge.py --once [PANEL]  print one panel (or `all`) and exit; colour if a terminal
    python3 tools/bridge.py --plain [PANEL] the same with no colour codes, for pasting into a reply
    python3 tools/bridge.py --check         draw every panel at several widths; exit 1 on any fault

Panels: status, queue, decisions, timing, fleet, leans. Everything is read from files in this
checkout; the display changes nothing. The look is in the spirit of the "LCARS" panels the founder
asked for: a block-colour side rail, pill labels, and bars. Standard library only.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PANELS = ["status", "queue", "decisions", "timing", "fleet", "leans"]
ORANGE, PEACH, LAV, BLUE, RED, GREEN, GREY, WHITE = 208, 216, 141, 110, 203, 114, 245, 231
RAIL = [ORANGE, PEACH, LAV, BLUE, PEACH, LAV]
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
    return fg(color, body) + fg(GREY, "·" * (width - vis(body)))


def spark(values):
    if not values:
        return ""
    top = max(values) or 1
    return "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v / top * 8 + 0.5))] for v in values)


def read(rel):
    f = ROOT / rel
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


def git(*args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, timeout=5).stdout.strip()
    except Exception:
        return ""


# ---- data, read fresh on every draw -------------------------------------------------------------

def queue_items():
    out = []
    for m in re.finditer(r"^- \*\*(SQ-(\d)\d\d) · (.*?)\*\*(.*)$", read("docs/ai-cto/superqueue.md"), re.MULTILINE):
        title, rest = m.group(3), m.group(4)
        state = "done" if "DONE" in rest or "DONE" in title else "blocked" if "BLOCKED" in title else "open"
        title = re.sub(r"^BLOCKED on [^·]*· ", "", title).rstrip(".")
        out.append({"id": m.group(1), "lane": {"0": "loop", "1": "you"}.get(m.group(2), "later"), "title": title, "state": state})
    return out


def decisions():
    out = []
    for m in re.finditer(r"^- \*\*(DEC-\d{3}) · (.*?) · (OPEN|GO|NO GO|MOOT)\b", read("docs/ai-cto/blocked.md"), re.MULTILINE):
        out.append({"id": m.group(1), "title": m.group(2), "status": m.group(3)})
    return out


def timings():
    rows = []
    for line in read(".claude/.matrix-times").splitlines():
        p = line.split("\t")
        if len(p) == 4:
            try:
                rows.append((p[2].split(".")[0], float(p[3])))
            except ValueError:
                pass
    return rows


def fleet():
    try:
        return json.loads(read(".claude/superfleet.json"))["scenarios"]
    except Exception:
        return []


def leans():
    out, tier = [], ""
    for line in read("docs/ai-cto/leans-e2e.md").splitlines():
        t = re.match(r"^## (Tier \d) · (.*)$", line)
        if t:
            tier = f"{t.group(1)} · {t.group(2)}"
        m = re.match(r"^(\d+)\. \*\*(.*?) \[(you|loop|both)\]\*\*", line)
        if m:
            out.append({"n": int(m.group(1)), "title": m.group(2).rstrip("."), "who": m.group(3), "tier": tier})
    return out


GATES = {"at": None, "rows": []}


def run_gates():
    rows = []
    for check in sorted((ROOT / "tools").glob("check-*.py")):
        t0 = time.time()
        try:
            ok = subprocess.run([sys.executable, str(check)], capture_output=True, text=True, cwd=ROOT, timeout=60).returncode == 0
        except Exception:
            ok = False
        rows.append((check.name, ok, time.time() - t0))
    GATES["at"], GATES["rows"] = time.strftime("%H:%M:%SZ", time.gmtime()), rows


# ---- panels: each returns a list of lines no wider than `w` -----------------------------------

def pill(color, text):
    return bg(color, f" {text} ")


def head(text, color=PEACH):
    return [pill(color, text.upper()), ""]


def panel_status(w):
    q, d = queue_items(), decisions()
    loop = [i for i in q if i["lane"] == "loop"]
    you = [i for i in q if i["lane"] == "you"]
    opens = [x for x in d if x["status"] == "OPEN"]
    mode = (re.search(r'"mode": "(\w+)"', read(".claude/cardinal-map.json")) or [None, "?"])[1]
    dirty = len(git("status", "--short").splitlines())
    t = timings()
    over = sum(1 for _, s in t if s > 10)
    k = lambda label: fg(GREY, f"{label:<14}")
    lines = head("status") + [
        k("branch") + bold(git("branch", "--show-current") or "(none)") + fg(GREY, "  at ") + git("log", "--format=%h", "-1"),
        k("gate mode") + fg(GREEN if mode == "warn" else ORANGE, mode) + fg(GREY, "   (labels and reminders; nothing is blocked)" if mode != "enforce" else ""),
        k("working tree") + (fg(GREEN, "clean") if not dirty else fg(RED, f"{dirty} file(s) not shipped")),
        "",
        k("loop's lane") + bar(sum(i["state"] == "done" for i in loop), len(loop) or 1, 24, GREEN) + f"  {sum(i['state'] == 'done' for i in loop)} of {len(loop)} done",
        k("your lane") + bar(sum(i["state"] == "done" for i in you), len(you) or 1, 24, LAV) + f"  {sum(i['state'] == 'done' for i in you)} of {len(you)} done",
        k("decisions") + fg(ORANGE if opens else GREEN, f"{len(opens)} open") + fg(GREY, f"  of {len(d)} logged") + ("   " + " ".join(fg(ORANGE, x["id"]) for x in opens) if opens else ""),
        k("tool calls") + (f"{len(t)} timed, " + fg(RED if over else GREEN, f"{over} over 10 s") if t else fg(GREY, "none timed on this machine")),
        "",
    ]
    nxt = next((i for i in loop if i["state"] == "open"), None)
    lines.append(k("next for loop") + (fg(WHITE, f"{nxt['id']} · {nxt['title']}") if nxt else fg(GREEN, "nothing open")))
    nxt = next((i for i in you if i["state"] == "blocked"), None)
    lines.append(k("next for you") + (fg(WHITE, f"{nxt['id']} · {nxt['title']}") if nxt else fg(GREEN, "nothing waiting")))
    lines += ["", pill(BLUE, "GATES") + ("  " + fg(GREY, "not run in this display; press g") if not GATES["rows"] else fg(GREY, f"  run at {GATES['at']}"))]
    for name, ok, took in GATES["rows"]:
        lines.append(f"  {fg(GREEN, '●') if ok else fg(RED, '✖')} {name:<26}" + bar(took, 10, 16, GREEN if took < 10 else RED) + fg(GREY, f" {took:4.1f}s"))
    return lines


def panel_queue(w):
    q = queue_items()
    lines = head("superqueue")
    marks = {"done": fg(GREEN, "✔"), "open": fg(ORANGE, "●"), "blocked": fg(GREY, "○")}
    for lane, label, color in (("loop", "THE LOOP'S LANE", ORANGE), ("you", "YOUR LANE", LAV), ("later", "AFTER YOUR LANE MOVES", BLUE)):
        items = [i for i in q if i["lane"] == lane]
        done = sum(i["state"] == "done" for i in items)
        lines.append(pill(color, label) + "  " + bar(done, len(items) or 1, 20, color) + fg(GREY, f"  {done}/{len(items)}"))
        for i in items:
            lines.append(f"  {marks[i['state']]} {fg(GREY, i['id'])}  {i['title']}")
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
        lines.append(f"  {fg(ORANGE, x['id'])}  {x['title']}")
    lines += ["", pill(GREEN, "DECIDED, NEWEST FIRST")]
    for x in [x for x in d if x["status"] != "OPEN"][:10]:
        lines.append(f"  {fg(GREY, x['id'])}  {fg(colors[x['status']], x['status'])}{' ' * (5 - len(x['status']))}  {x['title']}")
    return lines


def panel_timing(w):
    t = timings()
    lines = head("tool timing")
    if not t:
        return lines + [fg(GREY, "No tool calls have been timed on this machine."),
                        fg(GREY, "The stopwatch runs inside a Claude session in this checkout; its log is not in git.")]
    by = {}
    for card, secs in t:
        by.setdefault(card, []).append(secs)
    top = max(max(v) for v in by.values())
    scale = max(top, 10.0)
    width = max(10, min(40, w - 44))
    cap = int(10 / scale * width)
    lines.append(fg(GREY, f"{'':<10}{'calls':>5}  median  worst   0 s") + fg(GREY, " " * max(0, cap - 3)) + fg(RED, "│10 s cap"))
    for card in ("observe", "orient", "decide", "act"):
        v = sorted(by.get(card, []))
        if not v:
            continue
        b = bar(v[-1], scale, width, RED if v[-1] > 10 else GREEN)
        lines.append(bold(card) + " " * (10 - len(card)) + f"{len(v):>5}  {v[len(v) // 2]:5.2f}s {v[-1]:5.1f}s   {b}")
    over = [s for _, s in t if s > 10]
    lines += ["", fg(GREY, "last 60 calls  ") + fg(ORANGE, spark([s for _, s in t[-60:]])),
              "", pill(RED if over else GREEN, f"{len(over)} OF {len(t)} CALLS OVER 10 S") + (fg(GREY, "   worst ") + f"{max(over):.1f} s" if over else "")]
    return lines


def panel_fleet(w):
    f = fleet()
    lines = head("superfleet")
    if not f:
        return lines + [fg(GREY, "No fleet plan in this checkout.")]
    top = max(len(s["lanes"]) for s in f)
    for s in f:
        lines.append(f"{fg(ORANGE, s['id'])}  " + bar(len(s["lanes"]), top, 8, LAV) + f" {len(s['lanes'])}  {s['title']}")
    lines += ["", pill(LAV, f"{len(f)} SCENARIOS · {sum(len(s['lanes']) for s in f)} LANES") + fg(GREY, "   no lane has run; the lanes' instructions are the founder's to write")]
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
        lines.append(f"  {x['n']:>2}  {fg(colors[x['who']], x['who'])}{' ' * (4 - len(x['who']))}  {x['title']}")
    return lines


DRAW = {"status": panel_status, "queue": panel_queue, "decisions": panel_decisions,
        "timing": panel_timing, "fleet": panel_fleet, "leans": panel_leans}


def frame(panel, w, h=None, scroll=0):
    """The whole screen: top bar, side rail, the panel's body, bottom bar."""
    rail_w = 14
    body_w = w - rail_w - 2
    body = DRAW[panel](body_w)
    if h:
        room = h - 4
        scroll = max(0, min(scroll, max(0, len(body) - room)))
        more = len(body) - room - scroll
        body = body[scroll:scroll + room]
        body += [""] * (room - len(body))
    clock = time.strftime("%H:%MZ", time.gmtime())
    title = bg(ORANGE, " LOCALDNS BRIDGE ".ljust(rail_w + 1)) + " " + bg(PEACH, f" {panel.upper()} ")
    top = title + " " + fg(ORANGE, "━" * max(0, w - vis(title) - 10)) + " " + bg(LAV, f" {clock} ")
    out = [fit(top, w), ""]
    for row, line in enumerate(body):
        slot, sub = divmod(row, 2)
        if slot < len(PANELS):
            name = PANELS[slot]
            label = f" {slot + 1} {name.upper():<10}" if sub == 0 else " " * (rail_w - 1)
            cell = bg(WHITE if name == panel else RAIL[slot], label.ljust(rail_w - 1)) + (fg(WHITE, "▌") if name == panel else " ")
        else:
            cell = bg(GREY if row % 6 else ORANGE, " " * (rail_w - 1)) + " " if h else " " * rail_w
        out.append(fit(cell + " " + line, w))
    if h:
        keys = " Tab next · 1-6 jump · ↑↓ scroll · g gates · r refresh · q quit "
        foot = bg(ORANGE, keys) + " " + fg(ORANGE, "━" * max(0, w - len(keys) - 14)) + (" " + bg(PEACH, f" +{more} more ") if more > 0 else "")
        out += ["", fit(foot, w)]
    return out


def interactive():
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    idx, scroll = 0, 0
    sys.stdout.write("\x1b[?1049h\x1b[?25l")
    try:
        tty.setcbreak(fd)
        while True:
            w, h = shutil.get_terminal_size((100, 30))
            sys.stdout.write("\x1b[H\x1b[2J" + "\n".join(frame(PANELS[idx], w, h, scroll)))
            sys.stdout.flush()
            if not select.select([sys.stdin], [], [], 30)[0]:
                continue  # redraw twice a minute, so the clock and the files stay current
            ch = os.read(fd, 8).decode(errors="ignore")
            if ch in ("q", "Q", "\x03"):
                break
            if ch in ("\t", "\x1b[C"):
                idx, scroll = (idx + 1) % len(PANELS), 0
            elif ch in ("\x1b[Z", "\x1b[D"):
                idx, scroll = (idx - 1) % len(PANELS), 0
            elif ch in ("\x1b[B", "j"):
                scroll += 1
            elif ch in ("\x1b[A", "k"):
                scroll = max(0, scroll - 1)
            elif ch in ("\x1b[6~", " "):
                scroll += max(1, h - 6)
            elif ch == "\x1b[5~":
                scroll = max(0, scroll - max(1, h - 6))
            elif ch.isdigit() and 1 <= int(ch) <= len(PANELS):
                idx, scroll = int(ch) - 1, 0
            elif ch in ("g", "G"):
                sys.stdout.write("\x1b[H\x1b[2J  running the gates…")
                sys.stdout.flush()
                run_gates()
                idx, scroll = 0, 0
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


def check():
    global COLOR
    faults = []
    for color in (True, False):
        COLOR = color
        for w in (60, 80, 103, 160):
            for panel in PANELS:
                for h in (None, 24):
                    try:
                        lines = frame(panel, w, h)
                    except Exception as e:  # a panel must never take the display down
                        faults.append(f"{panel} at width {w}: {type(e).__name__}: {e}")
                        continue
                    wide = [l for l in lines if vis(l) > w]
                    if wide:
                        faults.append(f"{panel} at width {w}: {len(wide)} line(s) wider than the screen")
                    if not color and any("\x1b" in l for l in lines):
                        faults.append(f"{panel}: plain mode still holds colour codes")
    for f in faults:
        print("FAIL", f)
    if not faults:
        print(f"ok   bridge display: {len(PANELS)} panels drawn at 4 widths, framed and unframed, in colour and plain")
    return 1 if faults else 0


def main():
    global COLOR
    args = sys.argv[1:]
    if args[:1] == ["--check"]:
        return check()
    if args[:1] in (["--once"], ["--plain"]):
        COLOR = args[0] == "--once" and sys.stdout.isatty()
        want = args[1] if len(args) > 1 else "status"
        names = PANELS if want == "all" else [want]
        if any(n not in DRAW for n in names):
            print(f"FAILED: no panel {want!r}. Panels: {', '.join(PANELS)}, all")
            return 1
        w = min(shutil.get_terminal_size((100, 30)).columns, 120)
        for n in names:
            print("\n".join(l.rstrip() for l in frame(n, w)))
            print()
        return 0
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        COLOR = False  # piped or redirected: plain text, never colour codes in a file
        print("\n".join(l.rstrip() for l in frame("status", 100)))
        return 0
    interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
