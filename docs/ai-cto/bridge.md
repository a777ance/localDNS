# The bridge display

A text dashboard of the loop's state, for the founder's terminal: `tools/bridge.py`. Built
2026-11-12 at his request for briefings that are "pleasing to read and absorb". It reads files in
the checkout and changes nothing. The look follows the panel style he named: a block-colour side
rail, pill labels, and bars.

## Run it

Full screen, with panels to move through:

```bash
cd ~/localDNS
python3 tools/bridge.py
```

One panel printed and done (`status`, `queue`, `decisions`, `timing`, `fleet`, `leans`, or `all`):

```bash
cd ~/localDNS
python3 tools/bridge.py --once all
```

| Key | Does |
| --- | ---- |
| Tab, → | next panel |
| Shift-Tab, ← | previous panel |
| 1 to 6 | jump to a panel |
| ↑ ↓, PgUp PgDn | scroll a long panel |
| g | run all the gates and show each with its time |
| r | redraw now (it also redraws twice a minute) |
| q | quit |

## The panels

| Panel | Shows |
| ----- | ----- |
| status | branch, gate mode, unshipped files, both lanes' progress, open decisions, the next item for the loop and for the founder, and the gates |
| queue | the superqueue: the loop's lane, the founder's lane, and what waits behind them |
| decisions | how many are open, GO, NO GO, and moot, as bars; then each, newest first |
| timing | each cardinal's call count, median and worst time against the 10-second cap, and the last 60 calls as a strip |
| fleet | the ten superfleet scenarios and their lane counts |
| leans | the thirty leans by tier, and how many are the founder's, the loop's, or both |

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
- It has been drawn and checked at four widths by `tools/check-bridge.py`. It has not been seen on
  the founder's terminal as of 2026-11-12.
