#!/usr/bin/env bash
# Audit selected repo files against the live t630 without overwriting anything.
#
# Usage:
#   T630_HOST=USER@192.168.1.118 tools/t630-drift-audit.sh
#   T630_HOST=USER@10.8.0.1      tools/t630-drift-audit.sh
#
# The live t630 is the source of truth. This script only reads live files and
# writes timestamped diff artifacts under .audit/t630-drift/ for reconciliation.
# It uses sudo -n for root-owned files; warm the remote sudo ticket first with
# `ssh -t USER@192.168.1.118 sudo -v` if needed.
set -euo pipefail

T630_HOST="${T630_HOST:-USER@192.168.1.118}"
OUT_DIR="${OUT_DIR:-.audit/t630-drift/$(date -u +%Y%m%dT%H%M%SZ)}"

# repo_path|live_path|sudo_needed
FILES=(
  "01-core-network/unbound/server.conf|/etc/unbound/unbound.conf.d/server.conf|1"
  "01-core-network/unbound/tuning.conf|/etc/unbound/unbound.conf.d/tuning.conf|1"
  "01-core-network/unbound/remote-control.conf|/etc/unbound/unbound.conf.d/remote-control.conf|1"
  "01-core-network/unbound/root-auto-trust-anchor-file.conf|/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf|1"
  "01-core-network/unbound/streaming-forward.conf|/etc/unbound/unbound.conf.d/streaming-forward.conf|1"
  "01-core-network/unbound/local-records.conf|/etc/unbound/unbound.conf.d/local-records.conf|1"
  "01-core-network/host-dns/host-dns.conf|/etc/systemd/resolved.conf.d/host-dns.conf|1"
  "01-core-network/pihole/docker-compose.yml|~/pihole/docker-compose.yml|0"
  "04-user-services/ai-orchestration/docker-compose.yml|~/llm-router/docker-compose.yml|0"
  "04-user-services/ai-orchestration/config.yaml|~/llm-router/config.yaml|0"
  "04-user-services/console/index.html|/opt/console/index.html|1"
  "04-user-services/console/console.service|/etc/systemd/system/console.service|1"
  "04-user-services/console/ttyd-thinclient.service|/etc/systemd/system/ttyd-thinclient.service|1"
  "04-user-services/console/ttyd-laptop.service|/etc/systemd/system/ttyd-laptop.service|1"
)

mkdir -p "$OUT_DIR/live"
summary="$OUT_DIR/SUMMARY.md"
{
  echo "# t630 drift audit"
  echo
  echo "- Host: \`$T630_HOST\`"
  echo "- UTC: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo
  echo "| Status | Repo path | Live path | Diff artifact |"
  echo "| ------ | --------- | --------- | ------------- |"
} > "$summary"

status=0
for entry in "${FILES[@]}"; do
  IFS='|' read -r repo_path live_path sudo_needed <<< "$entry"
  if [[ ! -e "$repo_path" ]]; then
    printf '| missing repo | `%s` | `%s` | — |\n' "$repo_path" "$live_path" >> "$summary"
    status=1
    continue
  fi

  safe_name="${repo_path//\//__}"
  live_copy="$OUT_DIR/live/$safe_name"
  diff_file="$OUT_DIR/$safe_name.diff"

  if [[ "$sudo_needed" == "1" ]]; then
    remote_cmd="sudo -n cat '$live_path'"
  else
    remote_cmd="cat $live_path"
  fi

  if ! ssh "$T630_HOST" "$remote_cmd" > "$live_copy" 2> "$live_copy.stderr"; then
    printf '| unreadable live | `%s` | `%s` | `%s.stderr` |\n' "$repo_path" "$live_path" "live/$safe_name" >> "$summary"
    status=1
    continue
  fi

  if diff -u "$live_copy" "$repo_path" > "$diff_file"; then
    rm -f "$diff_file"
    printf '| match | `%s` | `%s` | — |\n' "$repo_path" "$live_path" >> "$summary"
  else
    printf '| differs | `%s` | `%s` | `%s` |\n' "$repo_path" "$live_path" "$(basename "$diff_file")" >> "$summary"
    status=1
  fi
done

echo "Wrote $summary"
exit "$status"
