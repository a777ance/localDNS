#!/usr/bin/env bash
# Audit selected repo files against the live t630 without overwriting anything.
#
# Usage:
#   T630_HOST=USER@192.168.1.118 tools/t630-drift-audit.sh
#   T630_HOST=USER@10.8.0.1      tools/t630-drift-audit.sh
#
# The live t630 is the source of truth. This script only reads live files and
# writes timestamped diff artifacts under .audit/t630-drift/ for reconciliation.
#
# Why it stages instead of `sudo -n cat`-ing each file: Ubuntu's sudo defaults to
# `timestamp_type=tty`, so a ticket warmed in one `ssh -t` session is invisible to
# the TTY-less `ssh host sudo -n ...` connections that follow. Every root-owned
# file then reports "unreadable" and the audit reads as catastrophic drift that
# isn't there. Instead: ONE interactive `ssh -t` copies every live file into a
# user-owned staging dir (sudo can prompt on that TTY), then ONE plain connection
# streams the whole staging dir back. One password, one tar, no false drift.
set -euo pipefail

T630_HOST="${T630_HOST:-USER@192.168.1.118}"
OUT_DIR="${OUT_DIR:-.audit/t630-drift/$(date -u +%Y%m%dT%H%M%SZ)}"

if [[ "$T630_HOST" == USER@* ]]; then
  echo "Set T630_HOST first, e.g. T630_HOST=alice@192.168.1.118 tools/t630-drift-audit.sh" >&2
  exit 2
fi

# repo_path|live_path   (a leading ~ is expanded on the BOX, not here)
FILES=(
  "01-core-network/unbound/server.conf|/etc/unbound/unbound.conf.d/server.conf"
  "01-core-network/unbound/tuning.conf|/etc/unbound/unbound.conf.d/tuning.conf"
  "01-core-network/unbound/remote-control.conf|/etc/unbound/unbound.conf.d/remote-control.conf"
  "01-core-network/unbound/root-auto-trust-anchor-file.conf|/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf"
  "01-core-network/unbound/streaming-forward.conf|/etc/unbound/unbound.conf.d/streaming-forward.conf"
  "01-core-network/unbound/local-records.conf|/etc/unbound/unbound.conf.d/local-records.conf"
  "01-core-network/host-dns/host-dns.conf|/etc/systemd/resolved.conf.d/host-dns.conf"
  "01-core-network/pihole/docker-compose.yml|~/pihole/docker-compose.yml"
  "04-user-services/ai-orchestration/docker-compose.yml|~/llm-router/docker-compose.yml"
  "04-user-services/ai-orchestration/config.yaml|~/llm-router/config.yaml"
  "04-user-services/console/index.html|/opt/console/index.html"
  "04-user-services/console/console.service|/etc/systemd/system/console.service"
  "04-user-services/console/ttyd-thinclient.service|/etc/systemd/system/ttyd-thinclient.service"
  "04-user-services/console/ttyd-laptop.service|/etc/systemd/system/ttyd-laptop.service"
)

mkdir -p "$OUT_DIR/live"
stage="/tmp/a777ance-drift-$$"

cleanup() { ssh "$T630_HOST" "rm -rf '$stage'" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# --- 1. one interactive session: stage every live file, readable by the login user
remote="set -u; rm -rf '$stage'; mkdir -p '$stage'; : > '$stage/.unreadable'; "
for entry in "${FILES[@]}"; do
  IFS='|' read -r repo_path live_path <<< "$entry"
  safe_name="${repo_path//\//__}"
  # a leading ~ must expand in the REMOTE shell, so emit it as $HOME
  remote_path="${live_path/#\~/\$HOME}"
  remote+="sudo cp -f -- \"$remote_path\" '$stage/$safe_name' 2>/dev/null || echo '$safe_name' >> '$stage/.unreadable'; "
done
remote+="sudo chown -R \"\$(id -u):\$(id -g)\" '$stage'"

echo "Staging live files on $T630_HOST (sudo may prompt once)..." >&2
ssh -t "$T630_HOST" "$remote"

# --- 2. one plain connection: stream the staging dir back (no sudo needed now)
ssh "$T630_HOST" "tar -C '$stage' -cf - ." | tar -C "$OUT_DIR/live" -xf -

unreadable_list="$OUT_DIR/live/.unreadable"
[[ -f "$unreadable_list" ]] || : > "$unreadable_list"

# --- 3. diff locally
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
  IFS='|' read -r repo_path live_path <<< "$entry"
  safe_name="${repo_path//\//__}"
  live_copy="$OUT_DIR/live/$safe_name"
  diff_file="$OUT_DIR/$safe_name.diff"

  if [[ ! -e "$repo_path" ]]; then
    printf '| missing repo | `%s` | `%s` | — |\n' "$repo_path" "$live_path" >> "$summary"
    status=1
    continue
  fi

  if grep -qxF "$safe_name" "$unreadable_list" || [[ ! -e "$live_copy" ]]; then
    printf '| absent on box | `%s` | `%s` | — |\n' "$repo_path" "$live_path" >> "$summary"
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
