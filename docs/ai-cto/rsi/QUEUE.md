# RSI-OODA: the lean queue

The open leans the passes draw from, ranked, most valuable first. `- [ ]` is open; `- [x]` is done, with the
pass or commit that closed it. **Refill rule** (founder's rule, 2026-11-15): when 2 or fewer leans are open, write
30 more before the next pass fires, so the loop never runs dry. That property has a name and a glyph:
**ongoing-OODA**, written **∆§** (founder's naming, 2026-11-15): the loop that refills itself and so never ends.
RSI-OODA is what each pass does; ongoing-OODA (∆§) is the guarantee that there is always a next pass. `tools/check-rsi.py` enforces it, and the commit
gate runs that check. Every lean says what would prove it wrong.

Numbering note: L-86 was used twice, for "long answers" (docs/ai-cto/leans-harness.md, end-to-end list) and for
pass 4's "complete headers" (the ledger). The second is L-86b from here on; L-132 keeps it from happening again.

## Refill 1 · 2026-11-15, 12:58 UTC (2 left: pass 5 and the harder shot, so 30 more)

- [x] **L-101 · Even out the calls (pass 5).** Done: pass 5, fastest yet (15.4 s), but the weight overshot; see L-133. Split questions by expected work, not count; pass 4's calls took
  8.9 s and 16.7 s. Target: pass 4's accuracy in 10 to 12 s. Wrong if: the slower call is slow for a reason the
  split cannot see.
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
