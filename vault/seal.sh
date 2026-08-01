#!/usr/bin/env bash
# Seal cleartext secrets into age-encrypted *.env.sops for committing.
#
# Usage:
#   ./seal.sh                 # seal every cleartext/*.env into <name>.env.sops
#   ./seal.sh pihole          # seal only cleartext/pihole.env -> pihole.env.sops
#
# Workflow: put plaintext in vault/cleartext/<name>.env (git-ignored), run seal,
# commit the resulting <name>.env.sops. The cleartext never leaves cleartext/.
# Requires: sops + age, and a valid recipient in .sops.yaml.
set -euo pipefail
cd "$(dirname "$0")"

command -v sops >/dev/null || { echo "sops not found — install sops + age first" >&2; exit 1; }
if grep -q 'age1CHANGE_ME' .sops.yaml; then
  echo "Refusing to seal: .sops.yaml still has the CHANGE_ME recipient." >&2
  echo "Set your real age public key in .sops.yaml (see README)." >&2
  exit 1
fi

mkdir -p cleartext
shopt -s nullglob

seal_one() {
  local name="$1" src="cleartext/${1}.env" dst="${1}.env.sops"
  [[ -f "$src" ]] || { echo "skip $name: $src not found" >&2; return 0; }
  sops --encrypt "$src" > "$dst"
  echo "sealed  $src -> $dst"
}

if [[ $# -gt 0 ]]; then
  for n in "$@"; do seal_one "$n"; done
else
  for f in cleartext/*.env; do
    n="$(basename "$f" .env)"; seal_one "$n"
  done
fi
echo "Done. Commit the *.env.sops files; never commit cleartext/."
