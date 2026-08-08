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

**Status: approve §2 only — §3 has grown.** Most stale refs are filed in a
`doom-drawer/2026-08-08` octopus commit in their own repo. Two groups are **not** safe to delete
and are held back below: **3 refs are unfiled** (deleting them orphans 17 commits), and **14 refs
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
| `claude/*` refs across ten repos (per `git ls-remote`) | **338** |
| …proven reachable from their repo's drawer | **335** |
| …**unfiled** (would orphan history if deleted) | **3** |
| …**filed but carrying an open PR** (deleting closes the PR) | **14** |
| …whose tip object could not be resolved | **0** |
| Superseded `archive/claude-sessions-*` labels, same commit as the drawer | 10 |
| **Refs safe to delete now** | **321 + 10 labels = 331** |
| Refs held back for review (§3) | **17** |

Re-measured 2026-08-08, per repo, iterating `git ls-remote --heads origin` and testing each tip
with `merge-base --is-ancestor <tip> <drawer>` after fetching the drawer fresh:

```
DESIGN-Full-Workflow-Integration-end-to-end-   claude=229  filed=226  UNFILED=3
localDNS  claude=49 filed=49  ·  MARKETING 13/13  ·  claude-code-homelab 13/13
customers 8/8  ·  Azure-lab 9/9  ·  Chronikomicon 7/7
Home-Sovereign-Full-Field-Guide 4/4  ·  Marketing-Strategy-1 3/3  ·  PRICING-MODELS 3/3
```

**The script itself is safe** — `retire-stale-branches.sh` re-tests reachability at run time and
`kept=$((kept+1)); continue`s on any unfiled ref, then warns. So running it will *not* orphan the
three. What was unsafe was this document telling the founder there was nothing to hold back. The
script protects history; it knows nothing about open pull requests, which is why §3 now carries
them.

---

## 2. Safe to delete — approve in this order

Ordered by **descending refs removed**, so the largest reductions land first and a partial
approval still buys the most. (This is a ranked list, not an alphabetical one, so house-style
Z→A ordering does not apply.)

"After" counts the repo once its `claude/*` refs **and** its superseded
`archive/claude-sessions-2026-08-08` label are gone; the drawer itself is **kept**.

| # | Repo | Refs now | `claude/*` filed | Drawer commit | After |
| - | ---- | -------- | ---------------- | ------------- | ----- |
| 1 | `DESIGN-Full-Workflow-Integration-end-to-end-` | 233 | 229 | `f3aa2734` | 3 |
| 2 | `localDNS` | 55 | 49 | `ba1ecd3b` | 5 |
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

### 3a. Unfiled — deleting these orphans history

Three `claude/*` refs in `DESIGN-…` are **not** reachable from that repo's drawer (`f3aa2734`).
Re-verified against `git ls-remote` tips, not a local checkout:

| Ref | Tip | Commits not in drawer | Commits not in `main` | Last commit |
| --- | --- | --------------------- | --------------------- | ----------- |
| `claude/exciting-mccarthy-bq9R0` | `d6fc46b6` | **9** | 9 | 2026-06-05 Adopt A777ance house style: Gill Sans MT + reverse-ordering |
| `claude/ai-cto-architecture-MZ2NF` | `a4e5dde` | **7** | 11 | 2026-06-04 NARF: schedule at 08:00 UTC |
| `claude/nifty-carson-Je7aG` | `84955bf` | **1** | 5 | 2026-06-04 Add PLUGINS.md: per-repo plugin guidance |

**17 commits exist only on these three refs.** File them into the drawer (re-run the archive step
against a clone that has fetched them) *before* any deletion pass, or exclude them explicitly.

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
