# RSI-OODA: the ledger

RSI-OODA is recursive self-improvement under the OODA loop, and it is never named or run without it: the gate, the
session's evaluation and the founder's trace chaperone every pass (founder's rule, 2026-11-15). One row per pass,
newest first. A pass is one turn of the gate (`tools/browser/explorer/GATE.md`): the explorer's
shot engine produces work, a session converts and evaluates it, commits what passed to `leader`, and restates the
page. OODA builds a better OODA. Speed and accuracy may trade against each other for a pass; the health of the
loop must point one way over the passes, and the numbers here are how anyone can see that it does.

The queue the passes draw from is `QUEUE.md`; its refill rule is ongoing-OODA (∆§), so there is always a next pass.

Rules for every pass:

- **Measure.** Fill every column from a measurement: the shot's result document, the run record
  (`runs/pass-N.json`, saved by the page and read by the session), or a check run by the session.
- **Name the trade before firing.** "Target" and "Trade accepted" are written before the shot goes out.
- **The loop never grades itself.** The page produces; the session evaluates against the repo; the founder's
  trace of the restated page closes the pass. Agreement inside the loop is not evidence (CLAUDE.md §G).

This folder lives in the repo, not in the page: the build leaves `docs/ai-cto/rsi/` out of the page's snapshot.

| Pass | Target · trade accepted | Shot | Accuracy (session's evaluation) | Speed | Cost | Defects found | Landed · closed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 · 13:03 UTC | Pass 4's accuracy in 10 to 12 s: split each wave by expected work, a read weighing 12 answers as pass 4 measured (L-101) · none | the same 23 tools | 23 of 23 accurate; new details checked in the headers (matrix.py's cap and lease, check-provenance.py's stale tags, DEC-020, Stage 10); 0 false | 15.7 s turn, shot 15.4 s, the fastest yet (pass 1: 16.1 s); first bundle 8.6 s · accuracy met, speed target missed | 2 calls, 1 read, 34,963 in / 4,996 out | split now uneven the other way: call 1 (one read, 5 answers) 8.2 s, call 2 (17 answers) 15.1 s; this pass puts a read at 4.3 answers, pass 4 at 12: one number is not enough | landed with the pass 5 record · closed by the run record (page commit `99330c3`) |
| 4 · 12:53 UTC | Pass 3's accuracy at pass 1's speed (about 16 s): attachments marked "complete header" answer header-only questions with no reads (L-86) · none | 23 tools | 23 of 23 accurate; the 4 gaps from complete headers; 8 "not stated" confirmed; `migrate.sh` now answered from its banner alone, as asked; 0 false | 18.4 s turn, shot 17.7 s (pass 1: 16.1 s); first bundle 13.7 s · accuracy target met, speed within 1.6 s of target | 2 calls, 1 read (`migrate.sh`, the one tool with no header), 34,960 in / 5,167 out | call 2 took 16.7 s, call 1 8.9 s: the split is uneven | landed with the pass 4 record · closed by the run record (page commit `adcb9e6`) |
| 3 · 12:40 UTC | Pass 2's accuracy at pass 1's speed: attach each file's whole header (L-85); reads only for real gaps · none | 23 tools | 23 of 23 accurate; the 4 gaps answered from the attached headers with 0 reads; 8 "not stated" confirmed; 0 false; `migrate.sh` answered from body comments, beyond the header the question named (facts correct) | 38.2 s turn; first bundle 27.8 s · accuracy target met, speed target missed (2.4 times pass 1) | 2 calls, 12 reads (all on the 9 files whose headers hold no run line), 34,436 in / 5,023 out | the prompt's "read before saying not stated" caused every read: the headers were already complete; reads all in call 1 (37.1 s) vs call 2 (24.0 s) | landed with the pass 3 record · closed by the run record (page commit `a271ba4`) |
| 2 · 12:20 UTC | Close pass 1's gaps by reading whole files (L-84) · time | 23 tools | 23 of 23 accurate; of 12 "not stated", 4 closed by reading, 8 confirmed true, 0 false | 92.0 s turn; first bundle 80.7 s | 2 calls, 35 reads, 25,788 in / 5,078 out | `commit: null` in bundles (shot started before repo.json); pass 1 gap count wrong (12, not 10) | `b69a948`, restated `d9e247e` · not separately traced; pass 3's run record names its page commit |
| 1 · 12:13 UTC | A real document from a shot: an index of `tools/` · none named | 23 tools | 23 of 23 accurate; 12 "not stated" (run command past 800 attached characters) plus `migrate.sh` (no header), filled by the session | 16.1 s turn; first bundle 13.9 s | 2 calls, 0 reads, 25,617 in / 4,145 out | engine sees only 800 characters per file | `4779e08`, restated `427feb4` · closed: trace 12:17:08 showed `4779e08` |

Started 2026-11-15; the 6 runs before the gate existed are measured in `docs/ai-cto/leans-harness.md`.
