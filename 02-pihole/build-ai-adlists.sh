#!/usr/bin/env bash
#
# Deploys to: ~/pihole/build-ai-adlists.sh   (run on the t630)
# Reload:     bash ~/pihole/build-ai-adlists.sh          (idempotent — safe to re-run)
# Cron:       weekly refresh — CDN/AI hosts churn, lists get new entries
#             0 4 * * 1  /usr/bin/bash /home/USER/pihole/build-ai-adlists.sh >/dev/null 2>&1
#
# Adds Firewalla's community AI blocklists (fw-public-lists) to THIS Pi-hole.
#
# WHY A SCRIPT AND NOT JUST THREE ADLIST URLS:
#   Two of the three source files are in Firewalla's own target-list syntax, one
#   entry per line as a leading-wildcard glob:  *.example.com
#   Pi-hole's gravity parser treats `*.example.com` as an INVALID domain and drops
#   it — so pointing Pi-hole straight at those raw URLs silently ingests ~0 domains.
#   This script converts them to ABP syntax (||example.com^), which Pi-hole v6 does
#   support and which blocks the apex + every subdomain (the intended semantics of
#   the `*.` glob). The third file (uBlock's) is already plain hosts format upstream,
#   so it is added as a remote adlist URL directly, no conversion.
#
# WHAT IT TOUCHES:
#   - writes converted lists INTO the running pihole container at /etc/pihole/ai-lists/
#     (that path is the persistent pihole_data volume, so they survive restarts)
#   - registers all three adlists in gravity.db (INSERT OR IGNORE — address is UNIQUE,
#     so re-runs never duplicate)
#   - rebuilds gravity (pihole -g)
#   It does NOT edit docker-compose.yml and needs no new bind mount.

set -euo pipefail

CONTAINER="${PIHOLE_CONTAINER:-pihole}"
DEST_DIR_IN_CONTAINER="/etc/pihole/ai-lists"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- sources -----------------------------------------------------------------
FW_BASE="https://raw.githubusercontent.com/firewalla/fw-public-lists/master"

# Firewalla wildcard-format files -> need *.x  ->  ||x^ conversion.
# format: "url|output-basename|adlist comment"
WILDCARD_LISTS=(
  "${FW_BASE}/nsfw-ai.txt|nsfw-ai.abp|AI: NSFW chatbots (Firewalla, wildcard->ABP)"
  "${FW_BASE}/ai-provider.txt|ai-provider.abp|AI: generative-AI providers (Firewalla, wildcard->ABP)"
)

# Already hosts-format upstream. Firewalla's ublockorigins-*.txt is only a redirect
# to this, so we consume the source of truth directly (no conversion, remote adlist).
UBLOCK_URL="https://raw.githubusercontent.com/laylavish/uBlockOrigin-HUGE-AI-Blocklist/main/noai_hosts.txt"
UBLOCK_COMMENT="AI: uBlockOrigin HUGE AI blocklist (hosts format, upstream)"

# --- preflight ---------------------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: pihole container '$CONTAINER' is not running." >&2
  echo "       start it first:  cd ~/pihole && docker compose up -d" >&2
  exit 1
fi

# convert a Firewalla wildcard list on stdin to ABP on stdout
# - drop comments (#...) and blank lines
# - strip a leading '*.'  (glob -> apex)
# - wrap as ||domain^   (Pi-hole ABP: blocks apex + all subdomains)
wildcard_to_abp() {
  awk '
    { gsub(/\r/, "") }
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    {
      sub(/^[[:space:]]+/, ""); sub(/[[:space:]]+$/, "")
      sub(/^\*\./, "")
      if ($0 == "") next
      print "||" $0 "^"
    }'
}

echo "==> preparing converted lists in the pihole container"
docker exec "$CONTAINER" mkdir -p "$DEST_DIR_IN_CONTAINER"

for entry in "${WILDCARD_LISTS[@]}"; do
  IFS='|' read -r url out comment <<<"$entry"
  echo "    - $url"
  curl -fsSL --max-time 60 "$url" -o "$TMP/src"
  wildcard_to_abp <"$TMP/src" >"$TMP/$out"
  count=$(wc -l <"$TMP/$out" | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    echo "ERROR: converted $out is empty — source format may have changed. Aborting." >&2
    exit 1
  fi
  echo "      -> $count domains"
  docker cp "$TMP/$out" "$CONTAINER:$DEST_DIR_IN_CONTAINER/$out"
done

# --- register adlists (idempotent) -------------------------------------------
register_adlist() {
  local address="$1" comment="$2"
  # address is UNIQUE in gravity.db; OR IGNORE makes re-runs a no-op.
  docker exec "$CONTAINER" pihole-FTL sqlite3 /etc/pihole/gravity.db \
    "INSERT OR IGNORE INTO adlist (address, enabled, comment) VALUES ('${address}', 1, '${comment//\'/\'\'}');"
}

echo "==> registering adlists in gravity.db"
for entry in "${WILDCARD_LISTS[@]}"; do
  IFS='|' read -r url out comment <<<"$entry"
  register_adlist "file://${DEST_DIR_IN_CONTAINER}/${out}" "$comment"
done
register_adlist "$UBLOCK_URL" "$UBLOCK_COMMENT"

echo "==> rebuilding gravity (this pulls the remote list and ingests the local ones)"
docker exec "$CONTAINER" pihole -g

echo "==> done. current AI adlists:"
docker exec "$CONTAINER" pihole-FTL sqlite3 /etc/pihole/gravity.db \
  "SELECT id, enabled, address FROM adlist WHERE comment LIKE 'AI:%';"
