#!/usr/bin/env bash
# Step 4 of the gate (GATE.md): restate leader into the explorer artifact.
#   bash tools/browser/explorer/restate.sh build            build HEAD as leader into build/explorer-out
#   bash tools/browser/explorer/restate.sh record VERSION   after publishing: write dist/ and SHA256SUMS
# Publishing itself needs the artifact tools, so a session does it between the two steps.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; root="$(git -C "$here" rev-parse --show-toplevel)"
out="${RESTATE_OUT:-$root/build/explorer-out}"
case "${1:-}" in
  build)
    [ -z "$(git -C "$root" status --porcelain -- . ':!tools/browser/explorer/dist')" ] || { echo "commit first: the page must equal a commit" >&2; exit 2; }
    rm -rf "$out"; EXPLORER_BRANCH=leader python3 "$here/build.py" "$out" >/dev/null
    echo "built $(git -C "$root" rev-parse --short HEAD) as leader into $out:"; (cd "$out" && sha256sum index.html repo.json heads.json bin.json)
    echo "next: publish_files with these four files, then: bash tools/browser/explorer/restate.sh record VERSION";;
  record)
    v="${2:?usage: restate.sh record VERSION}"; d="$here/dist"; mkdir -p "$d"
    cp "$out/index.html" "$out/heads.json" "$d/"
    { echo "# built from commit $(git -C "$root" rev-parse HEAD) on branch leader by tools/browser/explorer/build.py; published to the artifact as version $v on $(date -u +%F)"
      (cd "$out" && sha256sum index.html repo.json heads.json bin.json); } > "$d/SHA256SUMS"
    echo "wrote dist/ for version $v; commit it alone, push, then check: bash tools/browser/explorer/rebuild.sh";;
  *) echo "usage: restate.sh build | record VERSION" >&2; exit 2;;
esac
