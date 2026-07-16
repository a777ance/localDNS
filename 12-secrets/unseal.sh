#!/usr/bin/env bash
# Unseal the vault onto the live t630 — decrypt each vault/*.env.sops to its deploy
# path with the right permissions, per secrets.manifest.
#
# Run this ON the t630, at deploy/rebuild time, with the age identity available
# (USB mounted, SOPS_AGE_KEY_FILE exported). This is the "insert the wand" step.
#
#   sudo -E ./unseal.sh          # -E preserves SOPS_AGE_KEY_FILE through sudo
#
# For wg-inject rows it needs 05-wireguard/wg0.conf (the template with the
# REPLACE_WITH_SERVER_PRIVATE_KEY placeholder) present one level up in the repo.
set -euo pipefail
cd "$(dirname "$0")"

command -v sops >/dev/null || { echo "sops not found on the box — install sops first"; exit 1; }

MANIFEST="secrets.manifest"
WG_TEMPLATE="../05-wireguard/wg0.conf"

# Expand a leading ~ to the target user's home. Under sudo, HOME is often root's,
# so honor SUDO_USER when set so ~/llm-router lands in the real user's home.
expand_home() {
    local p="$1" home
    if [[ "$p" == "~/"* ]]; then
        home="$HOME"
        [[ -n "${SUDO_USER:-}" ]] && home="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
        printf '%s\n' "${home}/${p#\~/}"
    else
        printf '%s\n' "$p"
    fi
}

decrypt() { sops --decrypt --input-type dotenv --output-type dotenv "$1"; }

while IFS='|' read -r sealed target mode kind; do
    sealed="$(echo "$sealed" | xargs)"; target="$(echo "$target" | xargs)"
    mode="$(echo "$mode" | xargs)";     kind="$(echo "$kind" | xargs)"
    [[ -z "$sealed" || "$sealed" == \#* ]] && continue
    [[ -f "$sealed" ]] || { echo "skip: $sealed not in vault (seal it first)"; continue; }

    target="$(expand_home "$target")"
    install -d -m 700 "$(dirname "$target")"

    case "$kind" in
        file)
            umask 077
            decrypt "$sealed" > "$target"
            chmod "$mode" "$target"
            echo "unsealed: $sealed -> $target ($mode)"
            ;;
        wg-inject)
            [[ -f "$WG_TEMPLATE" ]] || { echo "wg template missing: $WG_TEMPLATE"; exit 1; }
            key="$(decrypt "$sealed" | sed -n 's/^WG_SERVER_PRIVATE_KEY=//p' | tr -d '"'"'"' ')"
            [[ -n "$key" ]] || { echo "no WG_SERVER_PRIVATE_KEY in $sealed"; exit 1; }
            umask 077
            # Substitute via an env var so the key never lands in the process list.
            WG_KEY="$key" awk '{ gsub(/REPLACE_WITH_SERVER_PRIVATE_KEY/, ENVIRON["WG_KEY"]); print }' \
                "$WG_TEMPLATE" > "$target"
            chmod "$mode" "$target"
            echo "unsealed: $sealed -> $target ($mode, key injected into wg0.conf)"
            ;;
        *)
            echo "unknown kind '$kind' for $sealed — skipping"; ;;
    esac
done < "$MANIFEST"

echo
echo "Done. Reload the services that consume these:"
echo "  sudo systemctl restart wg-quick@wg0"
echo "  ( cd ~/llm-router && docker compose up -d )"
echo "  sudo systemctl restart ttyd-thinclient ttyd-laptop"
echo "  ( cd ~/pihole && docker compose up -d )   # only once compose reads \${FTLCONF_webserver_api_password}"
