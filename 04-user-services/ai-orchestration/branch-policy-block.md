# Branch policy — the portfolio block (canonical)

**This file is the single source for the branch-policy section carried by every A777ance
repo's `CLAUDE.md`.** The policy is portfolio-wide — one promotion ladder across *every*
repo — so a copy that disagrees is not a stylistic difference, it is a session promoting
by the wrong path.

`tools/sync-briefings.py` renders the block below into each sibling repo between
`branch-policy:start` / `:end` markers. Those rendered blocks are **build output — never
hand-edit them.** Edit this file, re-run the generator, commit the result.

**Why a generator and not a checklist.** The predecessor rule ("push to `main`, no
branches") was written into two briefings and *absent* from the other eight. Absence is not
neutral: a session reading a briefing that says nothing about branching invents its own
answer, and the answer it invented 337 times was "cut a new `claude/*` branch." Silence is
an assignment. So the policy is given a site in every briefing, generated rather than
copied — see `docs/architecture/warrant-sites.md`.

**Scope — two tiers, deliberately.** This block is the *condensed* portfolio form. The
long form, with the Bifrost and Provenance reasoning behind it, stays in localDNS
`CLAUDE.md` §3; `tools/sync-briefings.py` asserts the two never contradict each other on
the rule itself.

<!-- branch-policy:start -->
**The cream rises — promote by cherry-pick, one rung at a time.** Founder's standing
instruction (2026-08-09), superseding "one standing working branch, no per-session
branches" (2026-08-08), which itself superseded "push to `main`, no branches"
(2026-06-05). The ladder is a *filter*: every promotion is a **cherry-pick — an act of
selection, never a bulk merge.** Merge moves everything; cherry-pick skims only what is
worth lifting. Nothing floats up by default; it has to be *chosen* up. That is how quality
rises rung by rung and the dross stays below.

**The ladder (raw → real):**

- **Feature branches** — many, cheap, per-session or per-topic. Where raw work happens.
  Multi-branch is legitimate again — but capped (below), and it never promotes by merge.
- **Doombox 1 — `doombox/1-messy`** — the messy box. Cherry-pick here the work you do not
  yet know what to do with. It inherits the doom drawer's role: *"Didn't Organize, Only
  Moved"* — nothing is sorted and so nothing is thrown away. The dated `doom-drawer/*` refs
  fold into this box. Retire a spent feature branch by cherry-picking (or filing) its tips
  here, then deleting the ref — history stays reachable, so the deletion loses nothing.
- **Doombox 2 — `doombox/2-draft-main`** — the draft main / pseudo-main. Cherry-pick here
  what is shaping up: the staging draft of what `main` will become.
- **`Yggdrasil`** — the exalted second standing branch; the **hyperspace**. *Everything
  must pass through it, and it is the only branch with access to `main`.* Cherry-pick from
  the doom boxes into Yggdrasil once you are satisfied.
- **`main` — the Well of Mimir** — vetted knowledge; the stable final repo. It moves only
  by a pull request the founder approves, cherry-picked up from Yggdrasil. No cadence, no
  auto-merge: the Well fills when the founder decides it does. This is the Bifrost one-way
  door at portfolio scale — `main` is the outermost `*`, and no inner gate may release past
  it. **`main` means "exists on the stable final repo," never "live."**
- **Valhalla** — *deployed, for real, on the box.* Not a branch: the state a change reaches
  only when it actually runs. `main` is the final ref; **Valhalla is the final reality.**

**Standing rules:**

- **The spring is the founder, and it is out of scope for the machine.** An analog signal
  nothing here can sample or verify against. Every rung is a *channel*, not a source; every
  file is **transmission**, and transmission never promotes. A green check proves
  transcripts agree with **each other** — never that they agree with the founder. Only
  asking closes that gap.
- **Never overwrite doctrine.** Pull with `--ff-only` and nothing else — a fast-forward can
  only *add* commits, where a merge, rebase, or reset can silently rewrite founder-authored
  text. A session transcribes doctrine; it does not author it.
- **The branch cap counts feature branches only.** No repo carries more than **9 feature
  branches**; the rails — `main`, `Yggdrasil`, and `doombox/*` — are promotion
  infrastructure and are exempt. The cap is what keeps re-legitimized branches from
  becoming the 337-branch sprawl again: branches are cheap because they are *capped*,
  *promoted by selection*, and *retired losslessly into Doombox 1*.
- **The tree is bigger than GitHub.** Yggdrasil spans the interacting systems — the t630
  stack, the LLM router, the NotebookLM bridge, Stripe, Setmore, the CRM — and GitHub is
  one root-well it drinks from.

**Push:** feature work goes to your own feature branch or straight into a doom box; you may
force-push a feature branch you own, **never a rail** (`main`, `Yggdrasil`, `doombox/*`).
Promote upward only by cherry-pick. Only Yggdrasil is offered to `main`, and only through
the founder's approved PR. Retry with backoff on network failure.
<!-- branch-policy:end -->
