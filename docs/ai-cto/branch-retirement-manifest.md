# Branch retirement manifest — founder approval queue

provenance: M · `tools/check-branch-cap.py` + `tools/retire-stale-branches.sh --dry-run` over all
ten repos checked out at the portfolio root · 2026-08-08 · verify: re-run both commands from a
root holding all ten full clones

**What this is.** The one-pass approval sheet for retiring the 338 stale `claude/*` refs. Every
number below was produced by running the tools, not read off an earlier document. Deletion is the
founder's call and is **not** taken here; nothing in this pass deleted a ref.

**Status: ready to approve.** All 338 stale refs are already filed in a `doom-drawer/2026-08-08`
octopus commit in their own repo, and each tip was individually re-verified reachable from it.
There is no unfiled branch anywhere in the portfolio, so no history depends on a `claude/*` ref
surviving.

---

## 1. The headline numbers

| Measure | Count |
| ------- | ----- |
| `claude/*` refs across ten repos | **338** |
| …proven reachable from their repo's drawer | **338** |
| …unfiled (would lose history if deleted) | **0** |
| …whose tip object could not be resolved | **0** |
| Superseded `archive/claude-sessions-*` labels, same commit as the drawer | 10 |
| **Total refs safe to delete** | **348** |
| Refs remaining portfolio-wide afterwards | 34 |

Verification command and its actual output:

```
$ ./tools/retire-stale-branches.sh --dry-run
deleted=338  kept(unfiled)=0  failed=0
```

`kept(unfiled)=0` is the load-bearing number: the script only counts a branch as deletable after
testing `merge-base --is-ancestor <tip> <drawer>` at run time, and it reported nothing held back.

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

| Ref | Repo | Why it is held back |
| --- | ---- | ------------------- |
| `archive/main-pre-consolidation` (`b6675cfb`) | `localDNS` | **Unique history.** Verified *not* reachable from the drawer, from `main`, or from `Yggdrasil`. Deleting it orphans the pre-consolidation snapshot. It is not a `claude/*` ref, so `retire-stale-branches.sh` will not touch it — its legacy-label cleanup globs `archive/claude-sessions-*` only. Keep, or promote to its own drawer before any decision. |

Nothing else is held back. The other ten `archive/claude-sessions-2026-08-08` labels were each
confirmed to point at **the identical commit** as that repo's `doom-drawer/2026-08-08`, so
retiring the label loses nothing — a claim the script asserted and this pass measured.

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
