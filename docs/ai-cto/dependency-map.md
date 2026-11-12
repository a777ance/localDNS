# Dependency map

Written 2026-11-12, about 01:50 UTC. What has to happen before what, across the thirty leans in
`docs/ai-cto/leans-e2e.md`, the open decisions in `docs/ai-cto/blocked.md`, and the old queue in
`docs/ai-cto/handoff.md`. The ordered work that follows from this map is `docs/ai-cto/superqueue.md`.

Numbers are lean numbers. "Hard" means the later item cannot be done without the earlier one. "Soft"
means it can be done but is worth less, or has to be redone.

## The four chains

```text
PRODUCT (the build)
  2 deploy volume layer ──hard──► 3 first real Statement
  7 mint Kuma key ───────soft──► 3   (without it, two of four figures are omitted, not faked)
  8 gate covers the rendered page ─soft─► 3   (the Statement is checked before a person keeps it)
  9 reconcile drift ─────hard──► any other deploy over a drifted file   (not needed for 2: its path is clean)
  10 exposure item · 11 VPN key and peers · 12 snapshot live-only · 13 seal secrets
        each needs the box, none needs another

INTENT (what the build is measured against)
  16 define promotion ───soft──► 1 intent onto main ──soft──► every later "is this what we meant?"
  15 default branch to leader      independent
  18 summarise old branches ─hard─► deleting any branch that holds unique work
  17 delete the six safe branches  independent

LOOP ENGINE (the loop turning without a prompt)
  4 attach repo to the schedule (DEC-018) ─hard─► a proving tick ─hard─► switching the schedule on
        ─soft─► 5 product-ratio rule   (the rule binds ticks; with no ticks it binds nothing)
  23 how sub-loops run (DEC-019) ─hard─► any sub-loop hand-out
        ─soft─► 26 goal-driven probe · 27 prose-rule audits   (these were the two items to be handed out;
                                                               a session can also just do them in turn)
  6 hook changes get the founder's eyes ─hard─► merging PR #58 by that rule, and every later hook change

LOOP COST AND QUALITY
  24 shrink sections G and H ◄─hard─ repoint tools/check-docs.py and tools/check-doctrine.py first
  22 one rule in, one rule out ─soft─► every later reply rule
  21 flag a run of acts · 25 cost in the session log · 19 branch names by cardinal · 20 no order rule
        independent of everything
```

## Every item, with what it needs and what it unblocks

| # | Item | Needs first | Unblocks | Who |
| - | ---- | ----------- | -------- | --- |
| 30 | Stop three habits | nothing | nothing; it is a standing correction | loop |
| 29 | Close DEC-005 | nothing | removes one open decision | you |
| 28 | Keep blocking mode off | nothing | nothing; it is a position | you |
| 27 | Audit the prose-only rules | nothing (soft: 23) | closes old queue item Q-035 | loop |
| 26 | One goal-driven probe | nothing (soft: 23) | the "adaptive" part of INIT-006 | loop |
| 25 | Cost in the session log | nothing | a ledger for lean 5 and for the schedule | loop |
| 24 | Shrink sections G and H | two checks repointed; your yes | the largest per-turn cost cut | both |
| 23 | Sub-loops one at a time (DEC-019) | your answer | 26, 27 as hand-outs; the L step's hand-out | you |
| 22 | One rule in, one rule out | your yes | caps the reply-rule count | both |
| 21 | Flag a run of acts | nothing | catches blind acting | loop |
| 20 | No order rule | nothing | nothing; it is a position | loop |
| 19 | Branch names by cardinal | nothing | the per-step view of branches | loop |
| 18 | Summarise the old branches | nothing | a safe decision on 17's harder half | loop |
| 17 | Delete six safe branches | nothing | less noise in every fetch | you |
| 16 | Define promotion | nothing | 1 | both |
| 15 | Default branch to leader | nothing | GitHub shows and targets the working branch | you |
| 14 | Do not sort leader and outer | nothing | nothing; it is a position (old Q-040 is parked) | loop |
| 13 | Seal the secrets | the box | a repo that can rebuild the box | you |
| 12 | Snapshot live-only assets | the box | a true rollback target | you |
| 11 | VPN key and peers | the box | removes a known-exposed key | you |
| 10 | Exposure item | the box | closes the urgent item on Track 4 | you |
| 9 | Reconcile drift | the box | every deploy over a drifted file | you |
| 8 | Gate covers the rendered page | nothing | 3, safely | loop |
| 7 | Mint the Kuma key | the Kuma settings page | two of the four figures on 3 | you |
| 6 | Hook changes get your eyes | your yes | merging PR #58 under that rule | both |
| 5 | Product-ratio rule | nothing (soft: 4) | keeps ticks on the product | loop |
| 4 | Attach repo to the schedule (DEC-018) | the Claude app | the unattended loop | you |
| 3 | First real Statement | 2 (hard); 7, 8 (soft) | the proof that the whole chain works | both |
| 2 | Deploy the volume layer | the box | 3 | you |
| 1 | Intent onto main | soft: 16 | the yardstick for everything else | both |

## What the map shows

- **Two roots hold up the build, and both are yours:** the box (items 2, 9 to 13) and the Claude
  app (item 4). No session can reach either.
- **The loop's own lane has no hard blockers.** Items 5, 8, 18, 19, 21, 25, 26, 27 and a draft of
  1 and 16 can all be done now, in any order.
- **Only one loop item sits on the product's critical path:** 8, the gate for the rendered page.
  It goes first.
- **Nothing depends on sorting `leader` and `outer`,** which is why it is parked.
