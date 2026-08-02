#!/usr/bin/env bash
# Unseal *.env.sops to the plaintext deploy paths listed in secrets.manifest.
#
# Usage:
#   ./unseal.sh                # unseal every sealed file to its deploy path
#   ./unseal.sh pihole         # unseal only pihole.env.sops
#   USER_HOME=/home/me ./unseal.sh   # override the USER placeholder in the manifest
#
# Reads secrets.manifest (sealed -> deploy path -> mode), decrypts each entry with
# sops (needs the age PRIVATE key at $SOPS_AGE_KEY_FILE or the sops default), writes
# the plaintext to the deploy path, and chmods it. Run on the t630 as the user that
# owns the deploy paths (sudo where a path is root-owned, e.g. /etc/a777ance).
set -euo pipefail
cd "$(dirname "$0")"

command -v sops >/dev/null || { echo "sops not found — install sops + age first" >&2; exit 1; }

# Replace the manifest's USER token with the real login (defaults to $USER).
user_repl="${USER_HOME:-/home/${SUDO_USER:-${USER}}}"

only="${1:-}"
while read -r sealed dest mode; do
  [[ -z "${sealed:-}" || "$sealed" == \#* ]] && continue
  name="${sealed%.env.sops}"
  [[ -n "$only" && "$name" != "$only" ]] && continue
  [[ -f "$sealed" ]] || { echo "skip $name: $sealed not present" >&2; continue; }
  dest="${dest/\/home\/USER/$user_repl}"
  mkdir -p "$(dirname "$dest")"
  sops --decrypt "$sealed" > "$dest"
  chmod "$mode" "$dest"
  echo "unsealed $sealed -> $dest (chmod $mode)"
done < secrets.manifest
echo "Done. Restart the affected services to pick up the new secrets."
