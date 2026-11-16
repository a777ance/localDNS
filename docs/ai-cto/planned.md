# Planned

Work that is designed and deliberately not started: a test or a build worth doing later, written down so it is
not re-derived and not lost. Started 2026-11-15 on the founder's word, to grow in parallel with the normal
building. Newest first. It is not the lean queue (`docs/ai-cto/rsi/QUEUE.md`, what RSI-OODA passes draw from next)
and not the decision list (`docs/ai-cto/blocked.md`, what only the founder can decide): an entry here is a design
waiting for its moment.

Every entry says what it **Needs** before it can start, when it is **Ready**, and what would prove it **Wrong**.
Status is one of `planned`, `ready`, `done` (with the commit or pass) or `dropped` (with the reason).
`tools/check-rsi.py` fails on a repeated id, an entry out of order, or an entry missing one of those lines.

## PLAN-003 · Count tokens in the page · ready

- **Why:** every cost figure so far is characters turned into tokens by a guess of 3.5 to 4 characters each.
- **Design:** the run record keeps the platform's usage figures for each call when it returns them, and the
  result document totals them. If the platform returns none, the record says so once and the estimate stays.
- **Needs:** nothing from the founder; one engine change and a restatement.
- **Ready when:** the next engine change is being made anyway (it can ride with L-158). Half done with pass 9's engine change: the run record now keeps each call's usage figures if the platform returns any; the totals wait on seeing what comes back.
- **Wrong if:** the platform gives the page no usage figures at all.

## PLAN-002 · The fair race: one Haiku call against the fleet · planned

- **Why:** pass 8's fleet found 75% of the hits for about 3 cents at list price. One Haiku call holding the same
  million characters would cost about five times that (the price step at 100,000 tokens); whether it finds more
  or fewer is unmeasured, and it is the like-for-like comparison.
- **Design:** the same 1000 slices and the same question as pass 8, as one call (`per_call` 1000, one lane), graded
  by the same rule. Compare recall on hits, time, and characters in and out.
- **Needs:** recall on two lanes fixed first (L-156), so the fleet races at its best.
- **Ready when:** a sparse sweep has scored 95% recall or better.
- **Wrong if:** the single call is cut off or refused for size, which is itself the answer.

## PLAN-001 · Two views, four lanes · ready

- **Why:** one view of the artifact runs 2 model calls at a time (`docs/ai-cto/rsi/runs/exp-width.json`), and frames
  inside the page get none (`runs/exp-frames.json`). The platform's refusal says "from this page", so a second
  view, on another device or in a browser beside the app, may have 2 lanes of its own. If so, the whole repo
  reads in about 52 s instead of about 104 s (L-137, L-138).
- **Design:**
  1. *Claiming.* Before a page runs a shot it writes `claimed_by` (a random id made at load) and `claimed_at` into
     the shot with a guarded update that fails if another page wrote first. A page skips a shot claimed by another
     id less than 5 minutes ago. Shots are claimed one at a time, just before running, not all at load.
  2. *The probe.* Two identical shots, each 2 calls of the count-to-200 work, written to the mailbox while both
     views are open. Each view claims one. The run records carry each page's id.
  3. *Reading it.* One call alone takes about 3.3 s and two together about 3.3 s. If both views finish their pair
     in about 3.3 s, measured on the wall clock across both records, lanes add. If the four calls finish in two
     steps about 3 s apart, the views share 2 lanes. A refusal ("too many sample calls") in either record also
     means shared.
  4. *If lanes add.* The sweep splits into one shot per view (`fleet.offset` and `fleet.count`), each view claims
     one, and the session joins the result documents.
- **Needs:** the founder holding the artifact open in two places at once for about a minute. The claiming change
  is built (2026-11-16), though not as first designed: the page's database offers no guarded write, so a claim is a
  document of its own (`kind: claim`, `claim_of`), a page yields to a fresh claim already there, and two that arrive
  together agree on the lowest (ts, page id). It is tested against a rival claim in one page; two real pages are
  what this test is for. The shot states and allowed moves (`SHOT_MOVES`) came with it: the one idea taken from
  the tensor-harness script reviewed that day, built here with a test that an illegal move is refused.
- **Ready when:** the founder says he has two views to hand.
- **Wrong if:** both views claim the same shot (claiming is broken), or the second view cannot call the model
  at all.
