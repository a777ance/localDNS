# Hlidskjalf — the high seat

provenance: M · `python3 tools/hlidskjalf.py --write` · 2026-08-11 14:26 UTC · verify: re-run it —
every figure regenerates from `git ls-remote` / `rev-list`, so nothing here depends on
what any clone has fetched. PR rows are O-tier from docs/ai-cto/pr-snapshot.json and
carry their capture time.

**The seat sees; the hand stays the founder's.** This board is generated — edit the
generator, `tools/hlidskjalf.py`, never this file. It ranks the decisions only the
founder can make; it takes none of them.

---

## The decisions (ranked by what each unblocks — not alphabetical, deliberately)

### 1. Promote the cream by cherry-pick — 10 repo(s) ahead of main

**Why now:** 10 repo(s) have a `main` whose briefing never mentions the ladder, so every fresh clone reads superseded doctrine and a stale briefing cannot tell that it is stale. But `main` moves ONLY by cherry-pick now: `tools/check-promotion.py` refuses a rail as head, so a whole-branch merge cannot land even if approved.

**The action, precisely:** Per repo: `git checkout -b promote/<topic> origin/main`, `git cherry-pick <the chosen commits>`, push that branch, PR it into `main`. Choose the cream — a promotion is a selection, not a transfer. FIRST CLOSE the 10 open whole-branch PRs, which the guard now refuses: Azure-lab #2, Chronikomicon #6, DESIGN-Full-Workflow-Integration-end-to-end- #4, Home-Sovereign-Full-Field-Guide #2, MARKETING #3, Marketing-Strategy-1 #2, PRICING-MODELS---ALL-THREE #2, claude-code-homelab #3, customers #2, localDNS #29.

**Unblocks:** The gate scripts, the two-tier Pages site, Hlidskjalf itself, and every doctrine block reaching the tier fresh sessions clone.
**Source:** M · rev-list per repo + tools/check-promotion.py (verified: a rail head exits 1)

### 2. Decide the 14 open PRs riding retired-class branches

**Why now:** A branch with an open PR is pending review, not stale. Deleting its head closes the PR and records 'closed' — indistinguishable from 'rejected' six months later. Retirement is blocked behind these.

**The action, precisely:** Merge or deliberately close each: Azure-lab #1 (Adopt the design-surface convention in the h…); Chronikomicon #5 (Adopt the design-surface convention in the h…); DESIGN-Full-Workflow-Integration-end-to-end- #3 (Point stage 00 at the design system, and cor…); Home-Sovereign-Full-Field-Guide #1 (Adopt the design-surface convention in the h…); MARKETING #1 (Add Master Amounts Calculator and pricing co…); MARKETING #2 (Adopt the design-surface convention in the h…); +8 more in the retirement manifest §3b. Branches involved: claude/amwins-ai-governance-vu5tk4, claude/design-workflow-integration-y8yxx7, claude/homelab-microbiology-metaphors-18cl3d, claude/master-amounts-calculator-okqphz, claude/settings-alignment-dh8eua.

**Unblocks:** The 321-ref deletion pass (branch-retirement-manifest §2).
**Source:** O · pr-snapshot.json, 2026-08-08T15:55:00Z

### 3. Run the retirement — 2 claude/* refs still standing

**Why now:** Every repo's drawer is pushed; deletion is lossless by construction and re-verified at run time by the script itself. A session cannot run it: ref deletion is HTTP 403 through the agent proxy — this one is physically yours.

**The action, precisely:** From a machine with normal git credentials: `./tools/retire-stale-branches.sh --dry-run`, read it, then run it without the flag. It re-tests reachability itself and keeps anything unfiled — never delete from a document's list, including this one.

**Unblocks:** Branch cap PENDING notices in every repo; a legible ref namespace.
**Source:** M · ls-remote per repo (drawer refs present in 10/10)

### 4. Flip the Pages switch for the working tier

**Why now:** The two-tier site builds both trees, but a push to Yggdrasil cannot deploy: the github-pages environment rejects the branch before a runner is assigned (observed: run 31253812598, ~1s, no logs). The trigger is main-only until the environment allows it.

**The action, precisely:** Repo Settings → Environments → github-pages → Deployment branches: add `Yggdrasil`; then add "Yggdrasil" back to the workflow's `branches:` list.

**Unblocks:** Auto-publish of /yggdrasil/ on every working-tier push.
**Source:** O · .github/workflows/pages.yml trigger vs. its own two-tier build

### 5. Refresh the PR snapshot — 71h old

**Why now:** The ref list ages while you read it; so does this.

**The action, precisely:** Re-capture docs/ai-cto/pr-snapshot.json from a GitHub-capable session.

**Unblocks:** Trustworthy PR decisions.
**Source:** O · snapshot captured 2026-08-08T15:55:00Z

---

## The realms (Z→A, house style)

| Repo | Ygg vs main | policy on `main` | `claude/*` refs | drawer | note |
| ---- | ----------- | ---------------- | --------------- | ------ | ---- |
| `PRICING-MODELS---ALL-THREE` | +9 | ❌ pre-policy | 0 | `428de717` | oldest unmerged 2026-08-08 |
| `Marketing-Strategy-1` | +9 | ❌ pre-policy | 0 | `c7be6a3a` | oldest unmerged 2026-08-08 |
| `MARKETING` | +9 | ❌ pre-policy | 0 | `b2c18532` | oldest unmerged 2026-08-08 |
| `localDNS` | +42/-6 | ❌ pre-policy | 2 | `ba1ecd3b` | oldest unmerged 2026-08-08 |
| `Home-Sovereign-Full-Field-Guide` | +9 | ❌ pre-policy | 0 | `54fe3fda` | oldest unmerged 2026-08-08 |
| `DESIGN-Full-Workflow-Integration-end-to-end-` | +9 | ❌ pre-policy | 0 | `22569bca` | oldest unmerged 2026-08-08 |
| `customers` | +10 | ❌ pre-policy | 0 | `c367a958` | oldest unmerged 2026-08-08 |
| `claude-code-homelab` | +9 | ❌ pre-policy | 0 | `dfe5716b` | oldest unmerged 2026-08-08 |
| `Chronikomicon` | +9 | ❌ pre-policy | 0 | `23422fdc` | oldest unmerged 2026-08-08 |
| `Azure-lab` | +9 | ❌ pre-policy | 0 | `2762fb10` | oldest unmerged 2026-08-08 |

PR snapshot: **24 open PRs**, captured 2026-08-08T15:55:00Z (70.5h old) via GitHub MCP, session_01DQFfkkSUPXDTgKizj6RfpF (per-repo list_pull_requests, state=open).

## Claimed lanes (norns.md §4, verbatim)

| When (UTC) | Session | Lane | Claim |
| 2026-08-08 15:0x | `01Bu1wcD` | Urðr → Verðandi | doom drawer built + pushed (all 10); branch cap; proxy register; force-push guard portfolio-wide |
| 2026-08-08 ~15:01 | `01Dg4r8i` | (assigned Urðr) | "archive the doom drawer (no deletions)" — **already complete when assigned**, see §5 |
| 2026-08-08 10:49→ | `01DQFfkk` | Verðandi | branch-policy block generator, `check-tiers.py`, Pages trigger correction |
| # | Race | Resolves by | Cost you accept |
| 1 | Two Norns push the branch at once | Git refuses the second (non-fast-forward). Fetch, **rebase yours onto theirs**, push. | A rebase per collision. Never `--force`: that does not pass the eye, it puts out the other Norn's. |
| 2 | Two Norns claim the same work | One file per claim; exactly one push fast-forwards. **That push is the licence.** | None. This is free — git already serialises it. |
| 3 | A holder ends while holding a licence | **The lease.** Stale = older than the lease **and** silent within the lease window. Then `--take` with a reason. | A dead holder blocks for at most one lease (default 4h). |
| 4 | Work needs to move between live Norns | **`--hand ITEM --to <session>`** — a push hand-off. The holder consents by definition, so no liveness test is needed. | The receiver is not asked. A hand-off is a gift, and the giver had the right to give it. |
| 5 | Two Norns edit the *same generated block* | **Unsolved.** Both regenerate `CLAUDE.md`, both conflict. Resolution is manual: take the remote file, re-run the generator, never hand-merge build output. | Nine conflicts in one round, observed 2026-08-08. Lanes reduce it; nothing prevents it. |

---

Companion instruments: `tools/weave.py` (a Norn's next-move dispatcher) ·
`docs/ai-cto/branch-retirement-manifest.md` (the deletion approval sheet) ·
`tools/check-tiers.py` (the drawer-depth check the gate runs).
