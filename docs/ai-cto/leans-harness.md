# Leans on the browser harness and the Stop hook

Written 2026-11-15, about 03:45 UTC, after four live traces from the in-browser explorer (the claude.ai
artifact that runs the hooks as JavaScript ports, `tools/browser/hooks.js`). The founder asked for 20
leans, ranked and sorted, and said to follow them. A lean is a stated position with its reason and the
check that would show it wrong. Ranked by value for the risk, highest first.

## The Stop hook (`.claude/hooks/decide-act.py`)

- **L-01 · Teach the ACT rule the letter-led headings.** `decide_items` matches only the word `Decide` and
  `act_lines` only `Act`, so a reply written in the letter form the style requires (`D · `, `A · `) is never
  checked: a live reply queued four options under `D · ` with no Act lines and passed. Wrong if: a letter-led
  reply with a short Act list still passes, or a word-led case in `tools/check-stop-hook.py` changes its verdict.
- **L-02 · End the Act section at the next letter step.** Today the Act count runs on until a markdown heading,
  so lines under `L · ` would count as Act lines once `A · ` is recognised. Wrong if: a list under `L · ` is
  counted as acted.
- **L-03 · Pin both with cases in `tools/check-stop-hook.py`.** One blocking case (letter-led queue, nothing
  acted), one allowing case (acted in full), one for the L boundary. Wrong if: the check passes with the fix
  reverted.
- **L-04 · Record it as DEBT-014, Done, in the same change.** The debt register is where a found defect lives.
  Wrong if: `tools/check-registers.py` or `tools/check-docs.py` fails on the entry.
- **L-05 · Leave the two escape lines as they are.** `Not rehearsed:` and `Stopping because:` each switch a
  whole rule off for the reply. That is the written rule, and narrowing it is the founder's call, not a fix.
  Wrong if: the founder asks for per-block exemptions.

## The JavaScript port (`tools/browser/hooks.js`)

- **L-06 · Port the fix the same day, byte for byte in behaviour.** The port exists to behave like the
  original; a fix in one is a drift in the other. Wrong if: `node tools/browser/test/parity.js` or either
  fuzz test shows a difference.
- **L-07 · Add letter-led replies to the parity cases and the Stop fuzz.** The fuzz never generated `D · ` or
  `A · `, which is why the parity tests could not see this. Wrong if: the fuzz still has no letter-led fragment.

## The trace

- **L-08 · Say "not checked" when a rule did not run, with the reason.** ACT with no Decide list, REHEARSE with
  a `Not rehearsed:` line, NEXT with a `Stopping because:` line, TILE with no tile. "pass" there is a false
  claim in a debugger. Wrong if: a rule that ran is shown as not checked, or one that did not is shown as pass.
- **L-09 · List what an escape line exempted.** When `Not rehearsed:` turns REHEARSE off, name the bash blocks
  it covered, so the trace shows what went unchecked. Wrong if: a block is listed that was checked.
- **L-10 · Add a summary row per question.** Model time, tool time, hook time, tool calls, rules fired,
  whether a revision happened. This is the analysis done by hand on every trace so far. Wrong if: the parts
  do not add up to the turn within a few milliseconds.
- **L-11 · Store the 17 KB preamble once in the exported JSON.** Every model span repeats it, which is most
  of a 100 to 190 KB export. Wrong if: the export can no longer show what a model call was sent.
- **L-12 · Keep the second-pass audit trace-only.** Claude Code lets the second pass through unread; the
  page must not be stricter than the harness it copies. Wrong if: the founder wants the page to enforce it.

## The page

- **L-13 · Republish only after a browser test of every change.** Each change so far was tested in headless
  Chromium with a scripted model before it went out. Wrong if: a published version throws on load.
- **L-14 · Do not prompt around a rule the hook enforces.** The preamble may say what the view cannot do;
  it should not coach the model past a rule. The hook is the authority. Wrong if: a preamble line tells the
  model how to avoid a rule rather than meet it.
- **L-15 · Leave the refeed text alone.** It tells the model to do the top superqueue item, which this view
  cannot do; the model already hands that to a real session. Rewriting it here would fork the founder's
  ritual. Wrong if: a reply claims to have done a queue item.

## The repo

- **L-16 · Leave `CLAUDE.md` untouched.** It is 3 bytes under its 60,000-byte budget (DEC-022), and nothing
  here needs it. Wrong if: a change here requires a line in it.
- **L-17 · Run the static checks after every change.** `check-stop-hook`, `check-docs`, `check-registers`,
  `check-provenance`, `check-cardinal` and the rest. Wrong if: any fails.
- **L-18 · Run the retrofit after the rule change.** INIT-007: a rule reaches backward. Wrong if:
  `python3 tools/matrix.py orient.retrofit` finds an existing file the fixed rule now flags and it is not
  reported.
- **L-19 · Commit locally and hand over a patch; the push is the founder's.** This session reads the repo
  anonymously and cannot push. Wrong if: the patch does not apply to `leader` at 71e6ccc.
- **L-20 · No fact checker.** The trace caught two factual slips (the `gate.sh` check count, the DEC-022
  byte budget), and no hook checks facts. Building one is a project, not a lean. Wrong if: slips like these
  reach a kept document.
