# The three branches

Decided by the founder on 2026-11-12 (DEC-015). This replaces the older rule "push to `main`, no branches".

| Branch | What it is | Who writes to it |
| ------ | ---------- | ---------------- |
| `main` | **Intent cold storage.** Emptied of working files. It will hold the intent and the original spec, so the work can always be measured against what was meant. | The founder only, by promotion. |
| `leader` | **The off-main leader branch.** Everything to do with the OODA loop and the Matrix lives and lands here. All Claude sessions open pull requests into it; the gates decide, no approval is needed. | Every session, through its own branch and a pull request. |
| `outer` | **The outer third.** The home for everything that is not OODA work: the DNS stack, the VPN, monitoring, the Statements. | Sessions doing that work. |

A fourth branch, `main-before-evacuation`, is a frozen copy of `main` as it stood at `cba76bb`
before any of this. It is the undo button. Do not write to it and do not delete it.

## How work moves

1. A session cuts its own branch from `leader` (or from `outer` for non-OODA work).
2. It probes, ships, and opens a pull request into that same branch. The nine gates must pass.
3. `main` changes only when the founder promotes something into it.

The delta between `main` and `leader` is the thing to study at promotion time:
`python3 tools/matrix.py observe.probe merge leader main` reports how far ahead `leader` is.

## State on 2026-11-12, and what is not done

- `leader` and `outer` were both cut from `main` at `cba76bb`, so **each starts as a full copy**.
  Nothing has been sorted yet: `leader` still holds the non-OODA files and `outer` still holds the
  OODA ones.
- **Sorting is not a one-shot.** The gates read across the whole tree: `tools/check-docs.py` checks
  every path named in `CLAUDE.md`, and `tools/check-doctrine.py` reads the Jury code under
  `04-user-services/`. Removing the non-OODA files from `leader` turns those gates red until they
  are repointed. That work is Q-040 in `docs/ai-cto/handoff.md`.
- **`main` is not emptied yet.** The change is prepared as a pull request and waits on DEC-016,
  because three things break the moment it merges unless they are moved first (see DEC-016 in
  `docs/ai-cto/blocked.md`).
- **The default branch is still `main`.** Only the founder can change it, in the repository's
  settings on GitHub. Until then, new cloud sessions start on `main`.
- Every other branch is listed and marked below. None was changed.

## Every other branch is superfluous

Founder's rule, 2026-11-12: three branches are canonical; the rest are marked superfluous or deleted.
This is the mark. Listed Z to A, as counted on 2026-11-12. None has been deleted: deleting a branch
cannot be undone from here, so it stays the founder's hand.

| Branch | Last commit | Commits `leader` does not have | Mark |
| ------ | ----------- | ------------------------------ | ---- |
| `style-reply-main` | 2026-11-11 | 0 | **Superfluous, safe to delete.** Everything on it is already in `leader`. |
| `promote/promotion-lock` | 2026-08-09 | 1 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `doom-drawer/2026-08-08` | 2026-08-08 | 201 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `decision-log-dec007` | 2026-11-11 | 0 | **Superfluous, safe to delete.** Everything on it is already in `leader`. |
| `cursor/setup-cloud-environment-fb62` | 2026-09-12 | 1 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `cloudflare/workers-autoconfig` | 2026-07-21 | 128 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `claude/youthful-hopper-7knhtn` | 2026-11-11 | 0 | **Superfluous, safe to delete.** Everything on it is already in `leader`. |
| `claude/serene-tesla-yvl22m` | 2026-11-12 | 0 after each merge | in use: this session's working branch; superfluous once the session ends |
| `claude/loki-norn-promotion-e9e8vf` | 2026-08-08 | 2 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `claude/localdns-helper-patch-c0j21a` | 2026-08-09 | 0 | **Superfluous, safe to delete.** Everything on it is already in `leader`. |
| `claude/gpu-rental-options-s9mpbn` | 2026-08-16 | 0 | **Superfluous, safe to delete.** Everything on it is already in `leader`. |
| `claude/gpu-rental-options-pslkxi` | 2026-08-16 | 3 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `claude/elegant-sagan-ul1tc6` | 2026-11-11 | 17 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `archive/main-pre-consolidation` | 2026-06-02 | 55 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |
| `Yggdrasil` | 2026-08-11 | 48 | **Superfluous, not safe to delete unread.** It holds work that is nowhere else. |

`main-before-evacuation` is not superfluous: it is the undo copy and stays.
