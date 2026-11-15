# RSI-OODA: the lean queue

The open leans the passes draw from, ranked, most valuable first. `- [ ]` is open; `- [x]` is done, with the
pass or commit that closed it. **Refill rule** (founder's rule, 2026-11-15): when 2 or fewer leans are open, write
30 more before the next pass fires, so the loop never runs dry. That property has a name and a glyph:
**ongoing-OODA**, written **∆§** (founder's naming, 2026-11-15): the loop that refills itself and so never ends.
RSI-OODA is what each pass does; ongoing-OODA (∆§) is the guarantee that there is always a next pass. `tools/check-rsi.py` enforces it, and the commit
gate runs that check. Every lean says what would prove it wrong.

Numbering note: L-86 was used twice, for "long answers" (docs/ai-cto/leans-harness.md, end-to-end list) and for
pass 4's "complete headers" (the ledger). The second is L-86b from here on; L-132 keeps it from happening again.

## Refill 2 · 2026-11-15, 20:30 UTC (the founder's ask: 20 leans toward 1000 in a minute, after the width probe)

Ranked. The probe (`runs/exp-width.json`) measured 2 calls running and 6 held per page; these leans work inside or around that.

- [x] **L-135 · Many answers per call.** Done: pass 7, 250 answers a call at about 300 characters a second a lane. Two lanes make about 430 characters a second; the lever is how much each call answers. One call of 177 titles, then 500. Wrong if: characters per second fall as the call grows.
- [x] **L-136 · Shorter answers.** Done: pass 7, 39 characters an answer (pass 6: 48). Drop the `pong N #` prefix: reply `N<tab>title`. Pass 6's 48 characters an answer becomes about 35. Wrong if: accuracy falls or the saving is under 20%.
- [ ] **L-155 · Read much, write little (pass 8).** Reading costs about 0.086 s per 1,000 characters and writing about 2 s (fitted from the probe and pass 7). Give each shard its own slice and have the model write only where it matters. Wrong if: the turn misses the cost model's prediction by more than 20%, or silence hides overlooked slices.
- [ ] **L-137 · Two pages, four lanes.** The refusal says "from this page". Run the width probe with the page open twice. Wrong if: both pages still share 2 running calls.
- [ ] **L-138 · Shard a shot across pages.** Each open page claims a slice of the asks with a versioned write, so pages never double-run. Needs L-137 true. Wrong if: two pages answer the same ask.
- [x] **L-139 · A repeat field.** Done: pass 7, `fleet` expands in the page. A shot names a corpus and a count; the page expands it, so 1000 asks are not typed by hand. Wrong if: expanded ids collide on re-fire.
- [x] **L-140 · Never ask for more than 6.** Done: `e2dc197`, capped at 6. Width 8 lost 2 calls to `rate_limited`. Cap at 6 and queue the rest in the page. Wrong if: a refusal still appears in a run record.
- [x] **L-141 · No reads when the header is complete.** Done: pass 7, `tools: false`, 0 reads, 998 of 1000. Pass 6's call 1 made 45 reads the other calls did without. Withhold the read tool when every ask in a call has a complete header. Wrong if: accuracy falls.
- [ ] **L-142 · Trim the input.** Pass 6 sent about 45,000 characters a call. Send only the first heading line for title asks, not the whole header. Wrong if: time to first character does not fall.
- [ ] **L-143 · Measure time to first character.** Split each call's time into wait-before-output and output, so input and output costs are separate facts. Wrong if: the platform gives no streaming signal.
- [ ] **L-144 · Skip the preamble for fleet calls.** The 18,112-character harness preamble rides on every call; a fleet ask may not need it. Wrong if: the Stop hook or format check starts failing.
- [ ] **L-145 · Answer without the model.** A title is the file's first `# ` line: the page can read it from `repo.json` in milliseconds. The model is only needed where judgment is. Wrong if: the founder wants the model's throughput itself measured.
- [ ] **L-146 · Model only for the hard tenth.** The page answers what a rule can (L-145) and sends the rest to the two lanes. Wrong if: the rule's answers disagree with the model's on a sample.
- [x] **L-147 · Jury off for fleet shots.** Done: pass 7, `jury: false`. Jury calls took lanes during the width-8 probe. A fleet shot checks by exact match afterwards instead. Wrong if: flagged answers go unfixed and accuracy falls under 95%.
- [ ] **L-148 · Why two answers were flagged.** Read the width-4 and width-8 bundles; the wording check or the count was wrong. Wrong if: neither is at fault.
- [x] **L-149 · Pipeline, not waves.** Done: pass 7, lanes refill as calls finish. Keep exactly 2 running and 4 waiting at all times, refilling as each finishes, so no lane idles between waves. Wrong if: the gain over waves of 2 is under 5%.
- [ ] **L-150 · Batch checkpoints.** Every 200 answers the page writes a result, so a dropped phone loses one batch. Wrong if: the writes cost more than 2% of the turn.
- [ ] **L-151 · Faster writes.** A database write is about 140 ms; 1000 answers in bundles of 50 is 20 writes, in ones is 1000. Fix the bundle size from that. Wrong if: bundle size shows no effect on the turn.
- [ ] **L-152 · Does a bigger model go faster per answer?** Same 177 titles on the quick tier and on Haiku by name, characters per second compared. Wrong if: they are within 10%.
- [ ] **L-153 · A session-side fleet.** This session can start its own agents, outside the page's limit of 2. Measure how many run at once here. Wrong if: it is also capped low, or costs far more per answer.
- [x] **L-154 · The honest ceiling.** Done: `e2dc197`, in `tools/telepathy/ARTIFACT-BUS.md`. Write the measured limit into `ARTIFACT-BUS.md`: 2 running, 6 held, about 40 calls a minute a page, so no plan promises more without a new measurement. Wrong if: a later probe moves the numbers and the file is not updated.

## Refill 1 · 2026-11-15, 12:58 UTC (2 left: pass 5 and the harder shot, so 30 more)

- [x] **L-101 · Even out the calls (pass 5).** Done: pass 5, fastest yet (15.4 s), but the weight overshot; see L-133. Split questions by expected work, not count; pass 4's calls took
  8.9 s and 16.7 s. Target: pass 4's accuracy in 10 to 12 s. Wrong if: the slower call is slow for a reason the
  split cannot see.
- [x] **L-134 · Throughput: the haiku superfleet (pass 6).** Done: pass 6, 177 of 177 in 32.6 s; width 4 bought nothing (the platform runs 2). One shot of every doc title (177), Claude Haiku by name
  (the founder named it), four calls at once. Target: the turn under 60 s with at least 95% exact. Wrong if: the
  platform still runs two at a time, so width buys nothing.
- [ ] **L-133 · Tune the read weight from every run record.** Pass 4 measured a read at 12 answers, pass 5 at
  4.3; one fixed number swings the split. Fit time = per-answer cost + per-read cost over every recorded call
  (four so far), use the fit, and record it in the ledger each pass. Target: pass 4's accuracy in 10 to 12 s.
  Wrong if: per-call overhead, not reads, drives the difference.
- [ ] **L-102 · A harder shot (L-100).** Every `[hook]` rule in CLAUDE.md with the line of `decide-act.py` that
  enforces it, or "none". Mechanically checkable. Wrong if: the answer cannot be cited line by line.
- [ ] **L-103 · Number the attached lines.** Attachments carry line numbers, so an answer can cite `path:line`.
  The groundwork for L-104. Wrong if: numbers cost more characters than they save in reads.
- [ ] **L-104 · Check citations on the page (L-88).** A cited line that does not exist, or does not hold what the
  answer quotes, is flagged and goes to the jury. Wrong if: real answers rarely cite.
- [ ] **L-105 · Retrieve passages, not only headers (L-85 in full).** The page searches the repo for a question's
  terms and attaches the matching lines, numbered. For questions headers cannot answer. Wrong if: answers then
  cite files the retrieval missed.
- [ ] **L-106 · Jury on substance (L-89).** For flagged or `complex` asks, a second juror answers blind; a third
  settles a split. Wrong if: two jurors share the first one's error more often than they catch it.
- [ ] **L-107 · Long answers between markers (L-86).** `=== N ===` blocks, so paragraphs and diffs survive. Wrong
  if: a marker appears inside an answer.
- [ ] **L-108 · Tier per question (L-87).** quick for lookups, default or complex for judgement. Wrong if:
  `modelApplied` shows the platform ignores it.
- [ ] **L-109 · Measure p for the engine (CLAUDE.md §G).** Fire the same shot k times; record how often the
  answers agree with the session's evaluation. A pass's accuracy is then a rate, not one draw. Wrong if: k runs
  cost more than the passes they would save.
- [ ] **L-110 · A health line per pass, computed.** `check-rsi.py` prints accuracy, shot time, reads and the trend
  across the ledger. Wrong if: one line hides a trade the table shows.
- [x] **L-111 · `check-rsi.py`, the site of the refill rule.** Ledger rows valid and newest first, a run file for
  every recorded pass, open leans above 2. Done: the commit that added this queue. Wrong if: a pass lands without its row.
- [ ] **L-112 · Fire and collect with a script.** The session hand-writes each shot's JSON; a small generator
  from a plain question list cuts the session's cost and typing errors. Wrong if: the artifact tools still need
  the JSON pasted anyway.
- [ ] **L-113 · Save run records verbatim.** Passes 3 and 4 were condensed by hand; a transcription slip would go
  unseen. Save the record as read. Wrong if: verbatim records grow the repo past what a pass is worth.
- [ ] **L-114 · One Python line, not two.** The page logs the Python block twice per load. Wrong if: the two
  lines come from different checks that both matter.
- [ ] **L-115 · No restate for record-only commits.** The page leaves `docs/ai-cto/rsi/` out of its snapshot, yet
  its commit label still changes; label the page with the last commit that touched the snapshot. Halves the
  restates. Wrong if: the founder wants the page to name the newest commit.
- [ ] **L-116 · repo.json load time.** 3.3 to 11.2 s on the phone across passes; measure, then split or compress.
  Wrong if: the time is the network, not the size.
- [ ] **L-117 · Start the hooks on what they read.** The harness waits for all of repo.json; the hooks read a
  handful of files. Load those first. Wrong if: a hook reads more than the list says.
- [ ] **L-118 · The page's briefing reports flags truthfully.** A flagged answer must make the page's own
  briefing say Partial (L-82); test it with a planted flag. Wrong if: it already does.
- [ ] **L-119 · Test the deadline on the real model.** A shot with a deadline it cannot meet must end `partial:
  deadline`. Wrong if: the platform cancels the call first.
- [ ] **L-120 · Re-measure the platform's parallel limit.** Two at a time was measured once (run 4). Try three.
  Wrong if: the limit varies by time of day, so one measurement says nothing.
- [ ] **L-121 · The session as a second executor (L-78).** The session answers part of a shot itself, beside the
  page's two calls. Wrong if: the session is slower than the page.
- [ ] **L-122 · The header-index shot as a template (L-74).** One line fires "index the tools in FOLDER". Wrong
  if: no second folder needs an index.
- [ ] **L-123 · tools/README.md stays complete.** A check that every `tools/*.py` and `tools/*.sh` has a row.
  Wrong if: tools are added rarely enough that review catches it.
- [ ] **L-124 · The proposal envelope (L-91).** The page returns a diff for a file; the session converts,
  evaluates and applies it. The page proposing, never writing. Wrong if: no shot ever needs a change.
- [ ] **L-125 · A load heartbeat closes the pass.** On load the page writes its commit to the database; the
  session reads it to confirm a restate without the founder pasting a trace. Wrong if: a heartbeat from the page
  is taken as the founder's check; it confirms the load, not the result.
- [ ] **L-126 · Prune the database.** Export, then delete bundles and run records over 30 days. Wrong if: the
  25,000-document limit stays far off.
- [ ] **L-127 · Usage from the platform.** If `sample` reports token usage, record it per call. Wrong if: it
  does not.
- [ ] **L-128 · A second judge for high-stakes passes.** A separate agent re-checks the session's evaluation
  before a pass that changes rules or code, not docs. Wrong if: it agrees every time; then it is a rubber stamp.
- [x] **L-129 · Name rule site.** A check that the bare abbreviation never appears without "-OODA" outside dated archives. Done
  in this commit, inside `check-rsi.py`. Wrong if: it flags a word that merely contains the letters.
- [ ] **L-130 · Answers in the founder's words.** A plain-English summary on any result he reads (L-94). Wrong if:
  he reads the parts anyway.
- [ ] **L-131 · One shot of real work per day.** Each day's first pass answers a question the founder would
  otherwise answer by hand. Wrong if: the queue has no such question.
- [x] **L-132 · No lean id used twice.** `check-rsi.py` fails on a repeated `L-NNN` across the lean files. Done in
  this commit. Wrong if: a deliberate cross-reference trips it.
