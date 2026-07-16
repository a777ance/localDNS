#!/usr/bin/env bash
# Seal every filled cleartext/ secret into vault/ as a sops+age dotenv.
#
# Run this on your workstation (where the filled cleartext lives), NOT the t630.
# The vault/*.env.sops output is safe to commit; cleartext/ is git-ignored.
#
# Prereqs: sops + age installed, .sops.yaml carrying your real age recipient, and
# SOPS_AGE_KEY_FILE pointing at your age identity (the USB/token). See README.
#
#   ./seal.sh              # seal all cleartext/*.env present
#   ./seal.sh ttyd         # seal only cleartext/ttyd.env
#
# Idempotent: re-sealing an unchanged secret just rewrites its vault twin.
set -euo pipefail
cd "$(dirname "$0")"

command -v sops >/dev/null || { echo "sops not found — install sops (README, Step 1)"; exit 1; }

shopt -s nullglob
sources=(cleartext/*.env)
[[ $# -gt 0 ]] && sources=("cleartext/$1.env")

[[ ${#sources[@]} -eq 0 ]] && { echo "nothing in cleartext/ to seal — copy a cleartext.example/*.example first"; exit 1; }

for src in "${sources[@]}"; do
    [[ -f "$src" ]] || { echo "skip: $src not found"; continue; }
    base="$(basename "$src")"                 # e.g. ttyd.env
    out="vault/${base}.sops"                  # e.g. vault/ttyd.env.sops
    if grep -q 'CHANGE_ME' "$src"; then
        echo "REFUSING to seal $src — it still contains CHANGE_ME. Fill it in first." >&2
        exit 1
    fi
    sops --encrypt --input-type dotenv --output-type dotenv "$src" > "$out"
    echo "sealed: $src -> $out"
done

echo
echo "Done. Commit the vault/*.env.sops files. Never commit cleartext/."
