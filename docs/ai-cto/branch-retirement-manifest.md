# Branch retirement manifest — founder approval queue

provenance: M · per-repo `git ls-remote --heads origin` for the ref list, `merge-base
--is-ancestor <tip> <drawer>` for each tip after a fresh drawer fetch, and the GitHub API for open
PRs · 2026-08-08 · verify: re-run those three from any clone — the results do not depend on what
the clone has fetched, which is exactly why they replaced the earlier
`retire-stale-branches.sh --dry-run` figures. That dry-run enumerates **local** refs, so it
under-reported by three branches the DESIGN clone had never fetched, and reported
`kept(unfiled)=0` when the true answer was 3. A measurement that varies with the observer's
checkout is not `M`.

**What this is.** The one-pass approval sheet for retiring the 338 stale `claude/*` refs. Every
number below was produced by running the tools, not read off an earlier document. Deletion is the
founder's call and is **not** taken here; nothing in this pass deleted a ref.

**Status: approve §2 only — §3 has grown.** All stale refs are now filed in a
`doom-drawer/2026-08-08` octopus commit in their own repo. Two groups are **not** safe to delete
and are held back below: **1 ref is unfiled because it is LIVE work** (§3a-bis), and **14 refs
carry an open pull request** (deleting one closes its PR and discards proposed work). A blanket
"delete all 338" is not the right approval.

> **Amendment, 2026-08-08 15:2x — an earlier revision of this file said "unfiled = 0" and "there
> is no unfiled branch anywhere in the portfolio." Both were wrong**, and wrong in the dangerous
> direction: they invited a blanket approval. The dry-run that produced them enumerates **local**
> refs, and the DESIGN clone it ran against had never fetched three `claude/*` branches — so they
> were not counted as kept, they were *invisible*. This is the same stale-clone class of bug that
> `check-branch-cap.py` was fixed for one commit earlier; the fix did not reach the retirement
> script's ref enumeration. Numbers below are re-measured over `git ls-remote` — the remote's own
> ref list — not over any local checkout.

---

## 1. The headline numbers

| Measure | Count |
| ------- | ----- |
| `claude/*` refs across ten repos (per `git ls-remote`, 15:3x) | **339** |
| …proven reachable from their repo's drawer | **338** |
| …**unfiled** — all now filed except one **live** branch (§3a-bis) | **1** |
| …**filed but carrying an open PR** (deleting closes the PR) | **14** |
| …whose tip object could not be resolved | **0** |
| Superseded `archive/claude-sessions-*` labels, same commit as the drawer | 10 |
| **Refs safe to delete now** | **321 + 10 labels = 331** |
| Refs held back for review (§3) | **17** |

Re-measured 2026-08-08, per repo, iterating `git ls-remote --heads origin` and testing each tip
with `merge-base --is-ancestor <tip> <drawer>` after fetching the drawer fresh:

Before the §3a fix — three refs in `DESIGN-…` unreachable from its drawer:

```
DESIGN-Full-Workflow-Integration-end-to-end-   claude=229  filed=226  UNFILED=3
```

After advancing that drawer (`f3aa273 → 22569bc`, fast-forward), and re-measured across all ten:

```
DESIGN-Full-Workflow-Integration-end-to-end-   claude=229  filed=229  UNFILED=0
localDNS   claude=50  filed=49  UNFILED=1  ← claude/loki-norn-promotion-e9e8vf, LIVE (§3a-bis)
MARKETING 13/13 · claude-code-homelab 13/13 · customers 8/8 · Azure-lab 9/9
Chronikomicon 7/7 · Home-Sovereign 4/4 · Marketing-Strategy-1 3/3 · PRICING-MODELS 3/3
```

**The script itself is safe** — `retire-stale-branches.sh` re-tests reachability at run time and
`kept=$((kept+1)); continue`s on any unfiled ref, then warns. It would not have orphaned the
three. What was unsafe was this document telling the founder there was nothing to hold back: the
script protects history, but the document is what gets approved. And the script knows nothing
about open pull requests — a PR is not a git fact — which is why §3b exists and why no amount of
reachability testing would have produced it.

---

## 2. Safe to delete — approve in this order

Ordered by **descending refs removed**, so the largest reductions land first and a partial
approval still buys the most. (This is a ranked list, not an alphabetical one, so house-style
Z→A ordering does not apply.)

"After" counts the repo once its `claude/*` refs **and** its superseded
`archive/claude-sessions-2026-08-08` label are gone; the drawer itself is **kept**.

| # | Repo | Refs now | `claude/*` filed | Drawer commit | After |
| - | ---- | -------- | ---------------- | ------------- | ----- |
| 1 | `DESIGN-Full-Workflow-Integration-end-to-end-` | 233 | 229 | `22569bca` (was `f3aa2734`, advanced §3a) | 3 |
| 2 | `localDNS` | 56 | 49 | `ba1ecd3b` | 6 — incl. the live branch in §3a-bis |
| 3 | `MARKETING` | 17 | 13 | `b2c18532` | 3 |
| 4 | `claude-code-homelab` | 17 | 13 | `dfe5716b` | 3 |
| 5 | `Azure-lab` | 13 | 9 | `2762fb10` | 3 |
| 6 | `customers` | 12 | 8 | `c367a958` | 3 |
| 7 | `Chronikomicon` | 12 | 7 | `23422fdc` | 4 |
| 8 | `Home-Sovereign-Full-Field-Guide` | 8 | 4 | `54fe3fda` | 3 |
| 9 | `Marketing-Strategy-1` | 8 | 3 | `c7be6a3a` | 4 |
| 10 | `PRICING-MODELS---ALL-THREE` | 7 | 3 | `428de717` | 3 |

Every repo lands at 3–5 refs — the 3–5 the briefing calls healthy, against a cap of 9.

**The drawer carries fewer parents than the repo has branches** (e.g. Azure-lab: 5 parents, 9
branches). That is correct and not a gap: where one stale tip was already an ancestor of another,
only the maximal tips need to be parents. Reachability was checked **per branch**, all 338, not
inferred from the parent list.

---

## 3. Needs review — do NOT bulk-delete

### 3a. Unfiled — RESOLVED 2026-08-08

Three `claude/*` refs in `DESIGN-…` were not reachable from that repo's drawer, carrying **17
commits that existed on no other ref**:

| Ref | Tip | Commits that were at risk |
| --- | --- | ------------------------- |
| `claude/exciting-mccarthy-bq9R0` | `d6fc46b` | 9 |
| `claude/ai-cto-architecture-MZ2NF` | `a4e5dde` | 7 |
| `claude/nifty-carson-Je7aG` | `84955bf` | 1 |

**Filed, not excluded.** An exclusion list is a promise someone has to honour at deletion time; a
drawer entry is a site. `doom-drawer/2026-08-08` in `DESIGN-…` was advanced `f3aa273 → 22569bc`,
an octopus commit whose **first parent is the previous drawer** — so the update is a
**fast-forward, not a force**, nothing previously filed became unfiled, and the tree is unchanged
(a drawer is a reachability device, not a merge of content). Re-verified after the push:
`claude=229 filed=229 UNFILED=0`.

### 3a-bis. The ref list ages while you read it

**A new `claude/*` branch appeared in `localDNS` during this verification pass** —
`claude/loki-norn-promotion-e9e8vf`, pushed 15:33, one commit ahead of `Yggdrasil`. It is **live
work by an active session, not a stale ref**: it is unfiled *because it is current*, and it must
not be filed as retired or deleted.

This is the standing condition, not an anomaly. Sessions are still **assigned** a `claude/*`
branch by the harness at creation, regardless of the branch policy telling them to push to
`Yggdrasil` — so the population keeps growing while any snapshot of it goes stale. Two
consequences for whoever runs the deletion:

- **Never delete from this document's ref list.** Run `retire-stale-branches.sh`, which
  re-enumerates and re-tests reachability at run time. The list below is evidence for a decision,
  never the input to a `git push --delete`.
- **Age the candidates.** A ref whose tip is newer than the drawer is probably a live session, not
  a stale branch. Reachability alone cannot tell those apart, and the difference is somebody's
  in-flight work.

### 3b. Open pull requests — deleting these discards proposed work

A branch with an open PR is not stale, it is **pending review**: deleting the head branch closes
the PR. `retire-stale-branches.sh` cannot see this — it tests git reachability, and a PR is not a
git fact. Verified via the GitHub API, 2026-08-08: **14 open PRs across all ten repos**, on five
distinct branch names.

| Branch | Open PRs | Note |
| ------ | -------- | ---- |
| `claude/design-workflow-integration-y8yxx7` | **10** — one in *every* repo (localDNS #25, DESIGN #3, MARKETING #2, claude-code-homelab #2, Azure-lab #1, customers #1, Chronikomicon #5, Home-Sovereign #1, Marketing-Strategy-1 #1, PRICING-MODELS #1) | A coordinated portfolio-wide design-surface change. Deleting the branch closes all ten at once. |
| `claude/homelab-microbiology-metaphors-18cl3d` | localDNS #26 | Microbiology collection |
| `claude/amwins-ai-governance-vu5tk4` | localDNS #17 | AI governance blueprint page |
| `claude/settings-alignment-dh8eua` | localDNS #20 | The Jury (§G) — likely superseded; confirm before closing |
| `claude/master-amounts-calculator-okqphz` | MARKETING #1 | Master amounts calculator |

**Decide the PR first, then the branch.** Merge it, or close it deliberately — either way the
decision is recorded. Deleting the branch makes the decision silently, and records it as
"closed", which is indistinguishable from "rejected" six months later.

### 3c. Unique non-`claude/*` history

| Ref | Repo | Why it is held back |
| --- | ---- | ------------------- |
| `archive/main-pre-consolidation` (`b6675cfb`) | `localDNS` | **Unique history.** Verified *not* reachable from the drawer, from `main`, or from `Yggdrasil`. Deleting it orphans the pre-consolidation snapshot. It is not a `claude/*` ref, so `retire-stale-branches.sh` will not touch it — its legacy-label cleanup globs `archive/claude-sessions-*` only. Keep, or promote to its own drawer before any decision. |

The ten `archive/claude-sessions-2026-08-08` labels were each confirmed to point at **the
identical commit** as that repo's `doom-drawer/2026-08-08`, so retiring the label loses nothing —
a claim the script asserted and this pass measured.

---

## 4. Who can actually run the deletion

Not a session. Ref deletion returns **HTTP 403** through the agent git proxy, so
`retire-stale-branches.sh` ships unrun by design. Run it from a machine with normal git
credentials:

```bash
./tools/retire-stale-branches.sh --dry-run   # re-read the numbers first
./tools/retire-stale-branches.sh             # then delete
```

It re-verifies reachability at run time rather than trusting this document, so an approval that
sits for a week cannot go stale into a deletion — anything unfiled by then is reported and kept.

Recovering something afterwards stays one command: `git branch <name> <sha>`, with the drawer
listing available from `git log --oneline doom-drawer/* --not origin/Yggdrasil`.
