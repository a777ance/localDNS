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

## Ten more, after the mailbox (2026-11-15, about 04:00 UTC)

The founder asked for ten more, ranked, and said to follow them. L-22, L-23 and L-24 are his to run;
L-28 is his decision.

- **L-21 · Put the page's source in the repo.** The page and its build lived only in one session's workspace
  and in the published artifact. Now `tools/browser/explorer/`. Wrong if: a fresh clone does not rebuild a
  byte-identical page with `build.py`.
- **L-22 · Make the next test a reply to `cloud`, not more building.** Both directions are proven for marking
  done; no message has yet gone from the page to a session. Wrong if: the reply does not arrive.
- **L-23 · Save the `telepathy-mail` skill, then test Cowork and local.** The two peers not yet tried. Wrong if:
  either has no artifact tools; then it keeps `telepathy_mcp.py` on its own machine.
- **L-24 · Push the patches before relying on the fixes.** Real sessions still run the old Stop hook. Wrong if:
  `git am` fails on `leader`.
- **L-25 · Thread replies with an `re` field.** One optional field holding the id answered; nothing existing
  changes. Wrong if: nobody ever replies to a reply.
- **L-26 · Sender names are unverified; keep the artifact private.** Recorded as a limit in
  `tools/telepathy/ARTIFACT-BUS.md`. Wrong if: the artifact is shared with anyone.
- **L-27 · Sessions check mail when asked, never on a timer.** The house rule is never poll; the page is live.
  Wrong if: a message waits unread over a day while a session was working.
- **L-28 · The parity tests become a gate by the founder's decision.** Adding them to `check-all.sh` or
  `gate.sh` changes what blocks a commit (SQ-104). Wrong if: the port drifts before he decides.
- **L-29 · Fix the `gate.sh` header.** It said three checks, listed four, and ran thirteen; a live answer
  repeated the error. Comment only. Wrong if: `check-docs` objects.
- **L-30 · No wake-up for sessions yet.** How the page's live channel admits a session is not documented, so
  building on it would be guessing. Wrong if: a trace shows mail waiting while a session sat open.

## Twenty for speed, after the 30-round run (2026-11-15, about 11:10 UTC)

The founder asked for twenty leans to make the ping pong faster, then said to follow them. The measured run:
29 questions in one write, answered in one page turn of 160.5 s, of which 95.4 s was tool time, nearly all of
it the 29 replies written one after another (three database round trips each). Ranked by time saved.
Done means built and tested in Chromium against a mock database with 400 ms per round trip.

- **L-31 · Write the replies in parallel, not in a row.** Done. Wrong if: the artifact database refuses
  concurrent writes to different documents (a FAILED line in the mail_reply result).
- **L-32 · Mark done without reading the message back.** The page's live copy already holds it. Done. Wrong
  if: a done mark lands on a message the live copy had not yet seen.
- **L-33 · Send the reply and the done mark together.** Done. Under 400 ms per trip, 29 replies went from
  34.1 s and 86 trips to 0.4 s of writing. Wrong if: a reply exists whose original is not marked done.
- **L-34 · Attach the files a message names.** The first 1,500 characters of up to 60 repo files named in the
  mail go into the turn's prompt, so the model reads them without a read_file step each. Done. Wrong if:
  answers get less exact than the 29 of 29 the run with read_file scored.
- **L-35 · Use the quick model tier for automatic turns.** The page may set `modelTier: "quick"` on its own;
  a founder's question still gets the default. Done. Wrong if: the next real run scores below 29 of 29, or
  the trace's model time does not fall.
- **L-36 · Ask for the shortest briefing the Stop hook accepts.** Output tokens cost time. Done. Wrong if: the
  Stop hook blocks an automatic turn's reply (a revision call in the trace).
- **L-37 · One write from the session, one read back.** Already the practice since the 30-round run; it is
  also what ends the approval taps. Wrong if: a run needs the session to react to each answer.
- **L-38 · The session does not poll.** It waits for the founder's word, then reads once. Wrong if: the
  founder would rather watch rounds arrive than tap once at the end.
- **L-39 · Keep automatic turns small in the chat history.** Only the first line of the prompt is kept, so
  later turns do not carry 29 attached files. Done. Wrong if: a later turn needs those files and re-reads them.
- **L-40 · Wait 1.5 s before answering a burst.** Mail arriving within that window lands in one turn. Done.
  Wrong if: one write's documents arrive more than 1.5 s apart and split into two turns.
- **L-41 · Show each automatic turn's time in Mail.** The log line gives the turn's seconds and the reply
  write's milliseconds, so the next run reads its speed without a trace. Done. Wrong if: nobody looks.
- **L-42 · Do not use `cache`.** It replays an identical call for 5 minutes; mail is never identical.
  Wrong if: the platform adds prompt caching under that name.
- **L-43 · Keep the full harness on automatic turns.** The preamble is about 20,000 characters; cutting it
  would buy little and lose the house rules. Wrong if: the trace shows first output arriving after more than
  half the model time.
- **L-44 · Leave the hooks alone.** All hooks together took 30 ms of 160 s. Wrong if: they pass 1 % of a turn.
- **L-45 · Leave tracing on.** Its steps cost microseconds. Wrong if: trace export gets slow on a phone.
- **L-46 · One reply call, not one per message.** The prompt asks for a single mail_reply with every entry,
  so the model makes one tool step for the writes. Done (prompt). Wrong if: the trace shows several.
- **L-47 · Raise the batch above 40 only when a run needs it.** Forty fits one turn's tool input easily.
  Wrong if: a run sends more than 40 at once and waits for a second turn.
- **L-48 · Questions that name files answer fastest.** A session that wants speed names the path; the
  attachment rule does the rest. Wrong if: real questions rarely name paths.
- **L-49 · Next frontier: start the turn while the page loads.** The run lost about two minutes to the
  founder reloading. Not built: a page cannot load itself. Wrong if: the page is already open when mail comes.
- **L-50 · Measure the next real run before more building.** Mock latency is a guess at the real database.
  Wrong if: the real run's reply write time is already under a second.

### Two more, from the first fast run's trace (11:12 UTC)

The trace showed: 19 s of model time to the one mail_reply call (no file reads), 9.9 s writing 60 documents
(the platform takes them about 165 ms apart, however they are sent), then at least 11 s of model time for the
briefing. The founder said build both.

- **L-51 · A reply marks its message handled.** No done write after replying, so 30 writes instead of 60.
  Done; the protocol in tools/telepathy/ARTIFACT-BUS.md says so. Wrong if: a peer reads only `done_at` and
  shows answered mail as new.
- **L-52 · A successful mail_reply ends an automatic turn.** The page stops the model and writes the
  briefing itself; the Stop hooks still check it. Done. Wrong if: the hook blocks the page's briefing, or the
  model's later text carried something the replies did not.

Measured, run 3 (11:16 UTC, founder's phone): 30 questions answered in one turn of 17.3 s (model 13 s to its one
mail_reply call, 4.2 s writing 30 replies, no briefing pass), 30 of 30 exact. The first batched run took 160.5 s.
L-35, L-51 and L-52 hold: the quick tier lost no accuracy, and the page's briefing passed the Stop hook.

## Ten more, for another 9x (2026-11-15, about 11:20 UTC)

Target: run 3 took about 18.8 s from the questions landing to the last reply saved (1.5 s burst wait, 13 s of
model time, 4.2 s writing 30 replies at about 140 ms each, the platform's pace however they are sent). 9x is
about 2.1 s. Where it comes from, ranked by seconds saved. Not built yet.

- **L-53 · Split the batch across parallel model calls.** Six calls of five questions each, all at once. Output
  time dominates, so 13 s should drop to about 3 s. Wrong if: the calls come back `rate_limited`, or their
  wall time is the sum and not the longest.
- **L-54 · One reply document per turn, not one per message.** `mail/<id>` with `replies: [{re, body}]`. One
  write, about 0.15 s, instead of 4.2 s; a reply in it marks its message handled. Wrong if: a peer cannot read
  the bundle, or one document's size limit cuts a large batch.
- **L-55 · One question document per send, too.** The session writes `asks: [...]` in one document; the page
  sees one snapshot and needs no burst wait, saving 1.5 s. Wrong if: a sender cannot gather its questions first.
- **L-56 · Drop the house-style preamble from automatic turns.** Since L-52 the page writes the briefing, so
  the model no longer needs the Briefing rules or CLAUDE.md: about 18,000 characters out of every call. Keep the
  mail rules and the repo tools. Wrong if: answers drift from the house's plain style.
- **L-57 · Number the messages, not their ids.** The model answers "3: ..." and the page maps 3 to its id,
  cutting about 25 characters of output per reply. Wrong if: the model mixes up the numbering.
- **L-58 · Ask for the reply body only, as plain lines.** No tool call and no JSON: each parallel call returns
  "N: answer" lines and the page parses them. Saves the tool round trip inside each call. Wrong if: a line fails
  to parse; then that message falls back to the tool path.
- **L-59 · Write each shard as it lands.** The first shard's replies are saved while the others still think.
  Wrong if: L-54's one document per turn makes this moot (then one document per shard).
- **L-60 · Attach less.** 800 characters per file instead of 1,500, and nothing for a file already attached in
  this turn. Wrong if: a run 3 style check drops below 30 of 30 exact.
- **L-61 · Measure end to end, not the turn.** From the session's write to the last reply saved, read from the
  documents' own timestamps, so the burst wait and the page's load count. Wrong if: the turn time already
  matches it.
- **L-62 · Keep the benchmark honest.** "First heading of a file" is mechanical; page code could answer it in
  milliseconds with no model at all. That would measure the pipe, not Claude, so the 9x target counts model-
  answered runs only. Wrong if: the founder wants the pipe's speed, which is a separate, easy number.

Built (11:30 UTC): L-53 to L-60 in the page, L-61 by reading the documents' timestamps, L-62 by keeping run 4
model-answered. Chromium, with a stand-in model that spends 300 ms per answer line and 140 ms per database
trip: 30 questions in one document answered in 2.2 s, 30 of 30 exact, 6 calls at once, 6 bundles. The run 3
design under the same stand-in is about 15 s. Run 4 on the real model decides it.

Projection: about 3 s of model time (L-53, L-56, L-57, L-58), 0.15 s writing (L-54), no burst wait (L-55):
about 3.2 s end to end, 6x. The last stretch to 9x rests on L-53 running six calls truly in parallel.

Measured, run 4 (11:22 UTC, founder's phone): one turn of 8.2 s for 30 questions (run 3: 17.3 s), so 2.1x, not 9x.
Titles 30 of 30 exact, but the reply format drifted in 4 of 6 calls ("pong 11; # ...", "pong 16 | # ..."), so a
strict "pong N # title" check scores 10 of 30. The bundles landed in pairs (11:23:01.0/01.4, 03.5/03.7, 05.9/06.1):
the platform ran two calls at a time, not six. L-53 is wrong as built; its fix is as many calls as run at once
(two), so each waits once. Also seen: repo.json took 2.8 s to load on the phone before any answering began.
Built after run 4 (11:30 UTC): two calls, not six (one wave); a stricter wording rule in the prompt and a
`flag` on any answer whose quoted phrase is missing or followed by anything but a space; heads.json (the
first 800 characters of every text file, 267 KB) so a mail turn starts without waiting for repo.json (2 MB).
Chromium, stand-in model limited to two calls at a time, repo.json held back 2.5 s: first call 0.5 s after
load, 5.2 s end to end, the two planted format slips flagged and no others.

## Twenty for a one-shot of one-shots (2026-11-15, about 11:40 UTC)

The founder named it: the page is a one-shot engine (systemd's `Type=oneshot`: start, finish, exit; nothing idles).
He asked for twenty leans to make it a one-shot of one-shots: every unit of work is itself a one-shot, units
compose, and one fire runs the whole tree to completion. Ranked by how much each makes that true. Not built yet.

- **L-63 · One envelope for every shot.** A shot is a document with `asks` and an id; its answer is a bundle with
  `replies`. Today's run 5 document already is one. Everything below composes because the shape never changes.
  Wrong if: a real use needs a shape the envelope cannot carry.
- **L-64 · A shot ends in exactly one state.** `answered`, `partial` or `failed`, written once with the reason;
  never a half-state a reader has to guess about. Wrong if: a reader still has to count bundles to know.
- **L-65 · An ask may itself be a shot.** An ask with its own `asks` becomes a child shot; the parent ends when its
  children end. This is the "of one-shots". Wrong if: no real question ever needs to split.
- **L-66 · One fire runs the whole tree.** The page walks the tree in waves as wide as the platform allows (two,
  measured), deepest first, inside one load. Wrong if: a tree outgrows one load; then it resumes on the next (L-69).
- **L-67 · Chains by reference.** An ask may say `from: <shot>.replies[n]`; it runs once that answer exists, with
  it attached. Pipelines in one fire. Wrong if: every real chain needs a human look in the middle.
- **L-68 · The manifest carries everything.** Files named, wording, tier, deadline: the executor needs no context,
  as `sample` itself is memoryless. Wrong if: answers need the page's chat history.
- **L-69 · Re-firing is safe.** Bundle ids come from the shot id and the call number, so a reload after a crash
  overwrites, never duplicates, and skips what is done. Wrong if: two pages fire the same shot at once.
- **L-70 · A deadline per shot.** Past it, the shot ends `failed: deadline`, so nothing hangs. Wrong if: deadlines
  fire on shots that would have finished.
- **L-71 · The jury as a child shot.** A flagged answer spawns a second-juror shot for that answer only; agreement
  ends it, disagreement goes to a third. Costs nothing on a clean run (your `jury/` README's rule). Wrong if: the
  second juror repeats the first one's slip.
- **L-72 · Deterministic checks are shots with no model.** The format flag, "is this line in the file", counts:
  page code answers them in milliseconds and stands in the tree like any other shot. Wrong if: their verdicts
  disagree with a model checker's on real answers.
- **L-73 · Memo by content.** Same ask, same file heads, same tier: reuse the stored answer, zero model time. Only
  for asks marked deterministic. Wrong if: a reused answer was wrong and gets copied forward.
- **L-74 · Named shot templates.** "titles", "summarise", "check claim": the sender writes one line and the
  template supplies the wording and the check. Wrong if: templates multiply faster than they are used.
- **L-75 · Provenance on every bundle.** Model tier applied, the repo commit the files came from, timings, calls.
  A shot is its own evidence. Wrong if: nobody ever reads it.
- **L-76 · Trace per shot.** The trace export groups spans by shot id, so one tap gives the whole tree's timing.
  Wrong if: the tree is too big to read on a phone.
- **L-77 · Cost per shot.** Calls, characters in and out, recorded with the provenance. Wrong if: the platform's own
  counts disagree.
- **L-78 · Any peer can execute.** A session (cloud, local, cowork) runs a shot addressed to it in its own turn,
  same envelope, same bundle. The page is one executor, not the only one. Wrong if: sessions cannot meet the
  latency the page does.
- **L-79 · A shot runner for senders.** The `telepathy-mail` skill gains two verbs: fire (one write) and collect
  (one read, flattened). Wrong if: senders still hand-write documents.
- **L-80 · One human act, named.** Opening the page is the only tap; everything else fires from it. Say so on
  the page. Wrong if: a platform wake-up appears, then L-49 is solved and this goes.
- **L-81 · Measure shots, not turns.** End to end per shot from document timestamps, and shots per minute.
  Wrong if: turn time already tells the same story.
- **L-82 · Keep it honest under composition.** A parent is `answered` only if every child is; a flagged child
  makes the parent `partial`, never hidden. Wrong if: a parent ever reads `answered` with a flag underneath.

Built (11:50 UTC): L-63 to L-72, L-75, L-77, L-80 to L-82 in the page; not built: L-73 (memo), L-74
(templates), L-76 (trace grouped by shot; spans carry the shot id in their names), L-78 (sessions executing),
L-79 (skill verbs, waits on the founder saving the skill). Chromium, stand-in model limited to two calls at a
time: a flat 30 answered in 5.7 s, 30 of 30 exact, the planted slip fixed by the jury; a tree with a chain in
two waves with parent 2 composed; a dangling `from` ends partial with its reason; a call failing twice ends the
first load partial (2 of 4), and a reload fires only the 2 missing, with no duplicate bundles.
