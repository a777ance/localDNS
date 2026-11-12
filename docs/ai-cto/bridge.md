# The bridge display

A text dashboard of the loop's state, for the founder's terminal: `tools/bridge.py`. Built
2026-11-12 at his request for briefings that are "pleasing to read and absorb". It reads files in
the checkout and changes nothing. The look follows the panel style he named: a block-colour side
rail, pill labels, and bars.

## Claude, served through this display

The founder's instruction, 2026-11-12: "I don't want the usual Claude out-of-the-box CLI, I want
Claude to serve OUR UI." The first panel, `console`, is that.

- Press `i`, type a message, press Enter. The message goes to Claude through `claude -p` with
  streamed JSON output, which is the documented way to run Claude Code with no screen of its own.
- The reply streams into the console panel. Each step Claude takes shows as a line, and the
  `live` panel shows the same steps by letter (O, OO, D, A) with their times, because the repo's
  hooks run in that mode too.
- Every later message resumes the same conversation. The cost so far is shown at the top.
- `x` stops Claude mid-turn. Quitting the display stops it too.

**Permissions.** With no screen of its own, Claude cannot stop to ask you whether it may edit a
file or run a command; a step that needs a yes is refused. The display passes no permission
setting by itself. To give one, set `BRIDGE_CLAUDE_ARGS` before starting it, for example:

```bash
cd ~/localDNS
BRIDGE_CLAUDE_ARGS="--permission-mode acceptEdits" python3 tools/bridge.py
```

Not rehearsed: this needs the `claude` command and your login, which the cloud container that
built it does not use. The console's handling of Claude's output is tested against a stand-in
that writes the same kind of stream.

**Inside Claude Code's own screen**, if you ever use it, the display can supply its status bar:
`python3 tools/bridge.py --statusline` prints two lines (branch, mode, open decisions, the next
queue item, a context bar, cost, and the trail of letters). To turn it on, the `statusLine` setting
in `.claude/settings.json` has to name that command; a session is not allowed to change that file,
so it is yours to add.

## Run it

Full screen, with panels to move through:

```bash
cd ~/localDNS
python3 tools/bridge.py
```

One panel printed and done (`console`, `status`, `live`, `queue`, `decisions`, `activity`,
`timing`, `branches`, `fleet`, `leans`, or `all`):

```bash
cd ~/localDNS
python3 tools/bridge.py --once all
```

| Key | Does |
| --- | ---- |
| Tab, → | next panel |
| Shift-Tab, ← | previous panel |
| 1 to 9, 0 | jump to a panel (0 is the tenth) |
| i | write a message to Claude; Enter sends, Esc cancels |
| x | stop Claude mid-turn |
| ↑ ↓ | pick an item (marked ▸); on a panel with none, scroll |
| Enter | open or close the picked item: its full text appears beneath it |
| PgUp, PgDn, Space | scroll a page |
| g | run all the gates and show each with its time |
| r | redraw now (it also redraws twice a minute) |
| ? | the keys |
| q | quit |

## The panels

| Panel | Shows | Opens to |
| ----- | ----- | -------- |
| console | Claude, served through this display: your messages, its replies, each step it takes | |
| live | calls in flight right now, the latest finished calls with their letters and times, and the trail of letters | |
| status | four headline tiles; branch, gate mode, unshipped files; both lanes' progress; the next item for the loop and for the founder; the gates | the next item's full text; each gate's last line |
| queue | the superqueue in three lanes, with a mark per item | the item's done-test |
| decisions | open, GO, NO GO, and moot as bars; then each, newest first | the decision's full record |
| activity | commits per hour over the last 24 hours as a column chart; the latest twelve commits | the files each commit changed |
| timing | each cardinal's call count, median and worst time against the 10-second cap; the last 60 calls as a strip; the slowest calls | |
| branches | the three canonical branches and the undo copy, with their tips; every other branch and whether it holds anything `leader` lacks | file count, and commits ahead and behind |
| fleet | the ten superfleet scenarios and their lane counts | the goal, the look-first step, every lane, and the review |
| leans | the thirty leans by tier, and whose each is | the lean's reason |

The timing panel is empty on a machine where no Claude session has run in this checkout: the
stopwatch's log is not in git.

## Suggested settings for GNOME Terminal

The founder's terminal on the XPS is GNOME Terminal with the default profile. These settings suit
the display; each is in Preferences, under the profile.

| Tab | Setting | Suggested | Why |
| --- | ------- | --------- | --- |
| Text | Initial terminal size | 120 columns, 36 rows | the display is drawn for at least 100 columns; at 80 the long titles are cut |
| Text | Custom font | on, a monospace font at 12 or 13 | the house font, Gill Sans MT, is proportional, and a terminal needs every character the same width or the bars and the rail break |
| Text | Cell spacing | 1.00 wide, 1.00 high | any taller and the block characters show gaps between rows |
| Text | Allow blinking text | Never | nothing in the display blinks, and other tools that do are a distraction |
| Text | Cursor shape, blinking | I-Beam, Off | a block cursor reads as part of a bar |
| Text | Terminal bell | off | |
| Colors | Use colors from system theme | off | lets the background be set |
| Colors | Background | black, or very dark | the panel colours (orange, peach, lavender, blue) are chosen for a dark ground; on the default aubergine the lavender is weak |
| Colors | Text | a warm off-white | softer than pure white beside the orange |
| Scrolling | Limit scrollback | 10,000 lines or unlimited | long gate output is otherwise lost |
| Scrolling | Scroll on output | off | so reading older output is not interrupted |

The display uses the terminal's 256-colour set, which does not change with the palette setting.

## Limits

- It is a viewer. It runs the gates on request; it ships nothing and decides nothing.
- **Seen working on the founder's terminal, 2026-11-12, 02:11 UTC.** He typed one word into the
  console; the real Claude answered through the display, in the repo's reply style, and the turn
  cost 0.32 dollars. Most of that is the briefing every session loads, so a one-word message is
  not cheap (lean 24).
- Two faults seen in that first screenshot were fixed the same hour: the tenth rail label ran one
  column wide, and the session-start hook named the old queue.
