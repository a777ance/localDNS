#!/usr/bin/env bash
# Rotate a secret: decrypt, let you edit the plaintext, re-seal, and clean up.
#
# Usage:
#   ./rotate-secrets.sh pihole        # edit + re-seal pihole.env.sops in place
#   ./rotate-secrets.sh --rekey       # re-encrypt ALL sealed files to the current
#                                     # .sops.yaml recipients (after adding/removing
#                                     # an age key) — no plaintext edit
#
# `sops` edits in place with your $EDITOR and never writes cleartext to disk. After
# rotating a value here, run unseal.sh on the box and restart the service, then
# rotate the underlying credential at the provider too where relevant.
set -euo pipefail
cd "$(dirname "$0")"
command -v sops >/dev/null || { echo "sops not found — install sops + age first" >&2; exit 1; }

if [[ "${1:-}" == "--rekey" ]]; then
  # Re-encrypt every sealed file to whatever recipients .sops.yaml now lists.
  shopt -s nullglob
  for f in *.env.sops; do
    sops updatekeys --yes "$f"
    echo "rekeyed $f"
  done
  echo "Done. Commit the updated *.env.sops."
  exit 0
fi

name="${1:?usage: rotate-secrets.sh <name> | --rekey}"
sealed="${name}.env.sops"
[[ -f "$sealed" ]] || { echo "$sealed not found" >&2; exit 1; }
sops "$sealed"   # in-place encrypted edit
echo "Edited $sealed. Now on the box: ./unseal.sh $name && restart the service."
echo "If this was a leaked credential, also rotate it at the provider."
