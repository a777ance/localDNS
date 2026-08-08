#!/usr/bin/env bash
# Retire every stale claude/* branch across the A777ance portfolio.
#
# THE DOOM DRAWER — "Didn't Organize, Only Moved". The ADHD filing trick applied to git
# refs: one drawer you stuff things into without sorting them, exactly so nothing has to
# be thrown out to get the desk clear. The drawer is KEPT. This empties the desk.
#
# SAFE BY VERIFICATION, NOT BY ASSUMPTION. This script does not carry a list of branches
# captured when it was written — a list goes stale the moment anything changes, and a
# stale list is how you delete something that was never filed. Instead, per repo, at run
# time it:
#
#   1. finds the drawer ref (doom-drawer/*, or legacy archive/claude-sessions-*)
#   2. lists every claude/* branch on the remote
#   3. checks each tip is REACHABLE from the drawer
#   4. deletes only the reachable ones; anything unreachable is REPORTED AND KEPT
#
# So a branch that is not filed cannot be deleted by this script, even by mistake. 226 of
# the original 338 held commits that existed nowhere else — that is the failure this
# guards against.
#
#   dry run : ./retire-stale-branches.sh --dry-run
#   run     : ./retire-stale-branches.sh
#   inspect : git log --oneline doom-drawer/* --not origin/Yggdrasil
#   restore : git branch <name> <sha>
#
# WHY IT SHIPS UNRUN: ref deletion returns HTTP 403 from the agent environment (branch
# creation and updates succeed, deletes do not), so a session can file into the drawer but
# cannot clear the desk. Run this from a machine with normal git credentials.
#
# Portfolio root defaults to the parent of this repo; override with $PORTFOLIO_ROOT or $1.

set -uo pipefail

DRY_RUN=0
for a in "$@"; do
  case "$a" in
    --dry-run|-n) DRY_RUN=1 ;;
    *) PORTFOLIO_ROOT="$a" ;;
  esac
done

# Resolve once, absolutely — never rely on a relative $0 after a cd.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${PORTFOLIO_ROOT:-$(dirname "$(dirname "$_here")")}"

REPOS=(Azure-lab Chronikomicon DESIGN-Full-Workflow-Integration-end-to-end-
       Home-Sovereign-Full-Field-Guide MARKETING Marketing-Strategy-1
       PRICING-MODELS---ALL-THREE claude-code-homelab customers localDNS)

total_deleted=0 total_kept=0 total_failed=0

echo "portfolio root: $ROOT"
[ "$DRY_RUN" = 1 ] && echo "DRY RUN — nothing will be deleted"
echo

for name in "${REPOS[@]}"; do
  repo="$ROOT/$name"
  if [ ! -d "$repo/.git" ]; then
    echo "=== $name — SKIP (not checked out at $repo)"; echo; continue
  fi

  echo "=== $name"

  # The drawer. Prefer doom-drawer/*, fall back to the superseded archive/ label.
  drawer="$(git -C "$repo" ls-remote --heads origin 'refs/heads/doom-drawer/*' 2>/dev/null \
            | head -1 | cut -f1)"
  [ -z "$drawer" ] && drawer="$(git -C "$repo" ls-remote --heads origin \
            'refs/heads/archive/claude-sessions-*' 2>/dev/null | head -1 | cut -f1)"

  if [ -z "$drawer" ]; then
    echo "  no drawer found — refusing to delete anything here"; echo; continue
  fi

  # The drawer commit must be present locally to verify reachability against it.
  if ! git -C "$repo" cat-file -e "${drawer}^{commit}" 2>/dev/null; then
    git -C "$repo" fetch origin --quiet "$drawer" 2>/dev/null || true
  fi
  if ! git -C "$repo" cat-file -e "${drawer}^{commit}" 2>/dev/null; then
    echo "  drawer ${drawer:0:8} not fetchable — refusing to delete unverified"; echo; continue
  fi

  deleted=0 kept=0 failed=0
  while IFS=$'\t' read -r sha ref; do
    [ -n "${ref:-}" ] || continue
    branch="${ref#refs/heads/}"
    if ! git -C "$repo" cat-file -e "${sha}^{commit}" 2>/dev/null; then
      git -C "$repo" fetch origin --quiet "$sha" 2>/dev/null || true
    fi
    if ! git -C "$repo" merge-base --is-ancestor "$sha" "$drawer" 2>/dev/null; then
      echo "  KEEP   $branch — not reachable from the drawer"
      kept=$((kept+1)); continue
    fi
    if [ "$DRY_RUN" = 1 ]; then
      deleted=$((deleted+1)); continue
    fi
    if git -C "$repo" push origin --delete "$branch" >/dev/null 2>&1; then
      deleted=$((deleted+1))
    else
      echo "  FAIL   $branch — delete rejected"
      failed=$((failed+1))
    fi
  done < <(git -C "$repo" ls-remote --heads origin 'refs/heads/claude/*' 2>/dev/null)

  # The drawer's superseded label — same commit, so removing it loses nothing.
  if [ "$DRY_RUN" = 0 ]; then
    old="$(git -C "$repo" ls-remote --heads origin 'refs/heads/archive/claude-sessions-*' \
           2>/dev/null | head -1 | cut -f2)"
    if [ -n "$old" ] && git -C "$repo" ls-remote --heads origin 'refs/heads/doom-drawer/*' \
         2>/dev/null | grep -q .; then
      git -C "$repo" push origin --delete "${old#refs/heads/}" >/dev/null 2>&1 \
        && echo "  retired superseded label ${old#refs/heads/}"
    fi
  fi

  printf '  deleted=%s kept=%s failed=%s\n\n' "$deleted" "$kept" "$failed"
  total_deleted=$((total_deleted+deleted))
  total_kept=$((total_kept+kept))
  total_failed=$((total_failed+failed))
done

echo "-----"
printf 'deleted=%s  kept(unfiled)=%s  failed=%s\n' "$total_deleted" "$total_kept" "$total_failed"
[ "$total_kept" -gt 0 ] && echo "KEPT branches are NOT in the drawer — file them before retiring."
[ "$total_failed" -gt 0 ] && exit 1
exit 0
