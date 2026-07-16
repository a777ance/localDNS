#!/usr/bin/env bash
# Shed the old skin, grow the new — regenerate the custodian payload.
#
# The Lazarus posture (stateless rebuild) undoes what an attacker PLANTS but not what
# they TOOK: the secrets survive a wipe by being redeployed unchanged. Rotation is the
# fix — a resurrected box wears a NEW skin, so any copied secret is already dead.
#
# Run on your WORKSTATION (it writes cleartext/, then re-seals). Then commit vault/ and
# run unseal.sh on the t630.
#
#   ./rotate-secrets.sh apps           # LiteLLM key + ttyd password + Pi-hole password
#   ./rotate-secrets.sh wg-server      # NEW server keypair (every peer must be updated!)
#   ./rotate-secrets.sh wg-peer mac    # NEW keypair for one peer (cheap — only that device)
#   ./rotate-secrets.sh all            # apps + wg-server
#
# `apps` and `wg-peer` are cheap and safe to run often. `wg-server` changes the tunnel
# identity: EVERY peer config must be updated with the new server public key or it stops
# connecting — so it is opt-in and loud.
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null || { echo "missing tool: $1"; exit 1; }; }
rand_key() { need openssl; printf 'sk-%s' "$(openssl rand -hex 24)"; }
rand_pw()  { need openssl; openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 28; }

# Copy a cleartext.example template into cleartext/ if the working file is absent, so a
# fresh checkout can rotate without a manual cp first.
ensure() {
    local f="cleartext/$1"
    [[ -f "$f" ]] || cp "cleartext.example/$1.example" "$f"
    printf '%s\n' "$f"
}

# In-place KEY=VALUE rewrite (value may contain / and +, so use a non-slash delimiter).
setkv() {
    local file="$1" key="$2" val="$3"
    if grep -q "^${key}=" "$file"; then
        VAL="$val" awk -v k="$key" 'BEGIN{FS=OFS="="}
            $1==k { print k "=" ENVIRON["VAL"]; next } { print }' "$file" > "$file.tmp"
        mv "$file.tmp" "$file"
    else
        printf '%s=%s\n' "$key" "$val" >> "$file"
    fi
}

rotate_apps() {
    local llm ttyd pih newkey newttyd newpih user
    llm="$(ensure llm-router.env)"; ttyd="$(ensure ttyd.env)"; pih="$(ensure pihole.env)"

    newkey="$(rand_key)"; setkv "$llm" LITELLM_MASTER_KEY "$newkey"
    echo "  LITELLM_MASTER_KEY  -> rerolled"

    user="$(sed -n 's/^TTYD_CRED=\([^:]*\):.*/\1/p' "$ttyd")"; user="${user:-odin}"
    newttyd="$(rand_pw)"; setkv "$ttyd" TTYD_CRED "${user}:${newttyd}"
    echo "  TTYD_CRED           -> rerolled (user '${user}' kept)"

    newpih="$(rand_pw)"; setkv "$pih" FTLCONF_webserver_api_password "$newpih"
    echo "  Pi-hole admin pw    -> rerolled"

    echo "  ANTHROPIC_API_KEY   -> NOT auto-rotated (reissue in the Anthropic console, then edit cleartext/llm-router.env)"
}

rotate_wg_server() {
    need wg
    local f priv pub
    f="$(ensure wg0-key.env)"
    priv="$(wg genkey)"; pub="$(printf '%s' "$priv" | wg pubkey)"
    setkv "$f" WG_SERVER_PRIVATE_KEY "$priv"
    echo "  WG server keypair   -> rerolled"
    echo
    echo "  !! NEW SERVER PUBLIC KEY: $pub"
    echo "  !! EVERY peer's [Peer] PublicKey (the SERVER key on the peer side) must become this,"
    echo "  !! or that peer stops connecting. Update each device's config, then on the t630:"
    echo "  !!   ./unseal.sh && sudo systemctl restart wg-quick@wg0"
}

rotate_wg_peer() {
    need wg
    local name="$1" priv pub psk
    [[ -n "$name" ]] || { echo "usage: rotate-secrets.sh wg-peer <name>"; exit 1; }
    priv="$(wg genkey)"; pub="$(printf '%s' "$priv" | wg pubkey)"; psk="$(wg genpsk)"
    echo "  Peer '$name' keypair -> generated (server keeps only the PUBLIC key)"
    echo
    echo "  1) In ../05-wireguard/wg0.conf, replace peer '$name' PublicKey with:"
    echo "        PublicKey = $pub"
    echo "  2) On the DEVICE, set its [Interface] PrivateKey to:"
    echo "        PrivateKey = $priv"
    echo "     (optional) shared preshared-key for this peer:"
    echo "        PresharedKey = $psk"
    echo "  3) t630:  sudo systemctl restart wg-quick@wg0   (no vault change — peer pubkeys live in wg0.conf)"
    echo
    echo "  This is the cheap path for the known-exposed laptop key and the unidentified .4-.6 peers."
}

seal_now() {
    echo; echo "Re-sealing rotated secrets into vault/ ..."
    ./seal.sh
}

case "${1:-}" in
    apps)      rotate_apps; seal_now ;;
    wg-server) rotate_wg_server; seal_now ;;
    wg-peer)   rotate_wg_peer "${2:-}" ;;   # no vault change → no reseal
    all)       rotate_apps; rotate_wg_server; seal_now ;;
    *) echo "usage: $0 {apps|wg-server|wg-peer <name>|all}"; exit 1 ;;
esac

echo
echo "Shed complete. Commit vault/, then on the t630: ./unseal.sh and restart the services."
