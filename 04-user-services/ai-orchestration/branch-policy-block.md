# Branch policy — the portfolio block (canonical)

**This file is the single source for the branch-policy section carried by every A777ance
repo's `CLAUDE.md`.** The policy is portfolio-wide — one working branch across *every*
repo — so a copy that disagrees is not a stylistic difference, it is a session pushing to
the wrong place.

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
**`Yggdrasil` is the one standing working branch. Always push there, never to `main`.**
Founder's standing instruction (2026-08-08), superseding "push to `main`, no branches"
(2026-06-05).

- **One super-branch for the whole portfolio**, in every repo — no per-session branches.
  The branch-per-session habit is what produced 337 stale `claude/*` branches, 226 of them
  carrying commits that exist nowhere else.
- **`main` is the Well of Mimir** — vetted knowledge. It moves only by a pull request the
  founder approves. No cadence, no auto-merge: the Well fills when the founder decides it
  does. This is the Bifrost one-way door at portfolio scale — `main` is the outermost `*`,
  and no inner gate may release past it.
- **The spring is the founder, and it is out of scope for the machine.** An analog signal
  nothing here can sample or verify against. Yggdrasil and the Well are *channels*, not
  sources; every file in a repo is **transmission**, and transmission never promotes. A
  green check proves transcripts agree with **each other** — never that they agree with the
  founder. Only asking closes that gap.
- **Never overwrite doctrine.** Pull with `--ff-only` and nothing else — a fast-forward can
  only *add* commits, where a merge, rebase, or reset can silently rewrite founder-authored
  text. A session transcribes doctrine; it does not author it.
- **The tree is bigger than GitHub.** Yggdrasil spans the interacting systems — the t630
  stack, the LLM router, the NotebookLM bridge, Stripe, Setmore, the CRM — and GitHub is
  one root-well it drinks from.

**Push:** always `git push -u origin Yggdrasil`; retry with backoff on network failure.
Never `git push` to `main`, and never force-push either branch.
<!-- branch-policy:end -->
