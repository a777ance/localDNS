# Hlidskjalf — the high seat

provenance: M · `python3 tools/hlidskjalf.py --write` · 2026-08-08 16:00 UTC · verify: re-run it —
every figure regenerates from `git ls-remote` / `rev-list`, so nothing here depends on
what any clone has fetched. PR rows are O-tier from docs/ai-cto/pr-snapshot.json and
carry their capture time.

**The seat sees; the hand stays the founder's.** This board is generated — edit the
generator, `tools/hlidskjalf.py`, never this file. It ranks the decisions only the
founder can make; it takes none of them.

---

## The decisions (ranked by what each unblocks — not alphabetical, deliberately)

### 1. Draw Yggdrasil into the Well — 10 repo(s) ahead of main

**Why now:** 10 of them have a `main` whose briefing never mentions Yggdrasil, so every fresh clone reads doctrine that predates the branch policy — and a stale briefing does not know it is stale.

**The action, precisely:** Approve the open Yggdrasil→main pull requests. Open Yggdrasil→main PRs awaiting you: Azure-lab #2, Chronikomicon #6, DESIGN-Full-Workflow-Integration-end-to-end- #4, Home-Sovereign-Full-Field-Guide #2, MARKETING #3, Marketing-Strategy-1 #2, PRICING-MODELS---ALL-THREE #2, claude-code-homelab #3, customers #2, localDNS #29.

**Unblocks:** The tier gap, the gate scripts, the two-tier Pages site, and every doctrine block land where fresh sessions actually read them.
**Source:** M · rev-list over freshly fetched origin refs, per repo

### 2. Decide the 14 open PRs riding retired-class branches

**Why now:** A branch with an open PR is pending review, not stale. Deleting its head closes the PR and records 'closed' — indistinguishable from 'rejected' six months later. Retirement is blocked behind these.

**The action, precisely:** Merge or deliberately close each: Azure-lab #1 (Adopt the design-surface convention in the h…); Chronikomicon #5 (Adopt the design-surface convention in the h…); DESIGN-Full-Workflow-Integration-end-to-end- #3 (Point stage 00 at the design system, and cor…); Home-Sovereign-Full-Field-Guide #1 (Adopt the design-surface convention in the h…); MARKETING #1 (Add Master Amounts Calculator and pricing co…); MARKETING #2 (Adopt the design-surface convention in the h…); +8 more in the retirement manifest §3b. Branches involved: claude/amwins-ai-governance-vu5tk4, claude/design-workflow-integration-y8yxx7, claude/homelab-microbiology-metaphors-18cl3d, claude/master-amounts-calculator-okqphz, claude/settings-alignment-dh8eua.

**Unblocks:** The 321-ref deletion pass (branch-retirement-manifest §2).
**Source:** O · pr-snapshot.json, 2026-08-08T15:55:00Z

### 3. Run the retirement — 339 claude/* refs still standing

**Why now:** Every repo's drawer is pushed; deletion is lossless by construction and re-verified at run time by the script itself. A session cannot run it: ref deletion is HTTP 403 through the agent proxy — this one is physically yours.

**The action, precisely:** From a machine with normal git credentials: `./tools/retire-stale-branches.sh --dry-run`, read it, then run it without the flag. It re-tests reachability itself and keeps anything unfiled — never delete from a document's list, including this one.

**Unblocks:** Branch cap PENDING notices in every repo; a legible ref namespace.
**Source:** M · ls-remote per repo (drawer refs present in 10/10)

---

## The realms (Z→A, house style)

| Repo | Ygg vs main | policy on `main` | `claude/*` refs | drawer | note |
| ---- | ----------- | ---------------- | --------------- | ------ | ---- |
| `PRICING-MODELS---ALL-THREE` | +9 | ❌ pre-policy | 3 | `428de717` | oldest unmerged 2026-08-08 |
| `Marketing-Strategy-1` | +9 | ❌ pre-policy | 3 | `c7be6a3a` | oldest unmerged 2026-08-08 |
| `MARKETING` | +9 | ❌ pre-policy | 13 | `b2c18532` | oldest unmerged 2026-08-08 |
| `localDNS` | +29 | ❌ pre-policy | 50 | `ba1ecd3b` | oldest unmerged 2026-08-08 |
| `Home-Sovereign-Full-Field-Guide` | +9 | ❌ pre-policy | 4 | `54fe3fda` | oldest unmerged 2026-08-08 |
| `DESIGN-Full-Workflow-Integration-end-to-end-` | +9 | ❌ pre-policy | 229 | `22569bca` | oldest unmerged 2026-08-08 |
| `customers` | +10 | ❌ pre-policy | 8 | `c367a958` | oldest unmerged 2026-08-08 |
| `claude-code-homelab` | +9 | ❌ pre-policy | 13 | `dfe5716b` | oldest unmerged 2026-08-08 |
| `Chronikomicon` | +9 | ❌ pre-policy | 7 | `23422fdc` | oldest unmerged 2026-08-08 |
| `Azure-lab` | +9 | ❌ pre-policy | 9 | `2762fb10` | oldest unmerged 2026-08-08 |

PR snapshot: **24 open PRs**, captured 2026-08-08T15:55:00Z (0.1h old) via GitHub MCP, session_01DQFfkkSUPXDTgKizj6RfpF (per-repo list_pull_requests, state=open).

## Claimed lanes (norns.md §4, verbatim)

| When (UTC) | Session | Lane | Claim |
| 2026-08-08 15:0x | `01Bu1wcD` | Urðr → Verðandi | doom drawer built + pushed (all 10); branch cap; proxy register; force-push guard portfolio-wide |
| 2026-08-08 ~15:01 | `01Dg4r8i` | (assigned Urðr) | "archive the doom drawer (no deletions)" — **already complete when assigned**, see §5 |
| 2026-08-08 10:49→ | `01DQFfkk` | Verðandi | branch-policy block generator, `check-tiers.py`, Pages trigger correction |

---

Companion instruments: `tools/weave.py` (a Norn's next-move dispatcher) ·
`docs/ai-cto/branch-retirement-manifest.md` (the deletion approval sheet) ·
`tools/check-tiers.py` (the drawer-depth check the gate runs).
