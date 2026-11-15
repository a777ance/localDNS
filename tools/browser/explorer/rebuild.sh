#!/usr/bin/env bash
# Rebuild the explorer artifact exactly as published, and prove it byte for byte.
#   bash tools/browser/explorer/rebuild.sh [OUT_DIR]
# Reads dist/SHA256SUMS (the four served files, and the commit they were built from), builds that commit in a
# temporary worktree, and compares every hash. Exit 0 only if all four match. OUT_DIR keeps the build.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(git -C "$here" rev-parse --show-toplevel)"
sums="$here/dist/SHA256SUMS"
rev="$(sed -n 's/^# built from commit \([0-9a-f]*\).*/\1/p' "$sums")"
[ -n "$rev" ] || { echo "no '# built from commit' line in $sums" >&2; exit 2; }
out="${1:-$(mktemp -d)}"; mkdir -p "$out"
wt="$(mktemp -d)"; trap 'git -C "$root" worktree remove --force "$wt" >/dev/null 2>&1 || true' EXIT
git -C "$root" worktree add -q --detach "$wt" "$rev"
python3 "$wt/tools/browser/explorer/build.py" "$out" >/dev/null
( cd "$out" && grep -v '^#' "$sums" | sha256sum -c - )
echo "rebuilt $rev into $out: all four files match the published artifact"
