#!/usr/bin/env bash
# Deploy and verify the nftables per-category volume layer on the live t630.
#
# Usage:
#   T630_HOST=USER@192.168.1.118 T630_USER=USER tools/deploy-volume-layer.sh
#   T630_HOST=USER@10.8.0.1      T630_USER=USER tools/deploy-volume-layer.sh
#
# This implements DEPLOY-QUEUE Stage 10: copy collect/, validate/load nftables,
# populate the sets, install cron entries, and print verification counters.
#
# Two things this script is deliberate about:
#   1. The remote half is scp'd as a FILE and run under `ssh -t`, not piped into
#      `bash -s` over a TTY-less connection. sudo reads its password from /dev/tty;
#      with no TTY it dies with "no tty present and no askpass program specified".
#   2. Cron goes into ROOT's crontab, not the login user's. collect_stats.py reads
#      /etc/pihole/pihole-FTL.db, runs `nft -j list counters` and `wg show`, and
#      writes /var/lib/a777ance — all root-only. populate_sets.py --apply needs
#      root to program the nft sets. Installed as the login user, both jobs fail
#      silently: the IP sets stop refreshing, their 24h element timeout ages them
#      out, and the counters quietly decay toward zero while the statement
#      pipeline keeps reading them. Jobs log to /var/log/a777ance/ rather than
#      /dev/null so a failure is visible instead of inferred from bad numbers.
set -euo pipefail

T630_HOST="${T630_HOST:-USER@192.168.1.118}"
T630_USER="${T630_USER:-USER}"
REMOTE_DIR="${REMOTE_DIR:-/home/$T630_USER/a777ance/collect}"
LOCAL_DIR="docs/statements/tools/collect"

if [[ "$T630_HOST" == USER@* || "$T630_USER" == "USER" ]]; then
  cat >&2 <<'MSG'
Set both T630_HOST and T630_USER first, for example:
  T630_HOST=alice@192.168.1.118 T630_USER=alice tools/deploy-volume-layer.sh
MSG
  exit 2
fi

if [[ ! -d "$LOCAL_DIR" ]]; then
  echo "missing $LOCAL_DIR; run from the repo root" >&2
  exit 2
fi

ssh "$T630_HOST" "mkdir -p '$REMOTE_DIR'"
scp -r "$LOCAL_DIR/"* "$T630_HOST:$REMOTE_DIR/"

runner="$(mktemp)"
trap 'rm -f "$runner"' EXIT
cat > "$runner" <<'REMOTE'
set -euo pipefail
remote_dir="$1"
cd "$remote_dir"

# --- ruleset: validate, then load
sudo nft -c -f nftables-accounting.nft
sudo nft -f nftables-accounting.nft

# --- sets: dry-run first (resolves DNS, touches nothing), then apply
python3 populate_sets.py >/tmp/a777ance-populate-sets.nft
test -s /tmp/a777ance-populate-sets.nft
sudo python3 populate_sets.py --apply
sudo nft -j list counters table inet a777acct >/tmp/a777ance-counters.json

sudo install -d -m 755 /var/lib/a777ance
sudo install -d -m 755 /var/log/a777ance

# Optional secret for the nightly collector. Uptime Kuma's /metrics is authenticated;
# with no key collect_stats.py gets 401 and uptime/latency stay null forever. Created
# empty + 0600 so the cron line can source it unconditionally; fill in on the box.
if ! sudo test -e /etc/a777ance/collect.env; then
  sudo install -d -m 755 /etc/a777ance
  printf '# KUMA_KEY=CHANGE_ME   # Uptime Kuma > Settings > API Keys\nKUMA_KEY=\n' \
    | sudo tee /etc/a777ance/collect.env >/dev/null
  sudo chmod 600 /etc/a777ance/collect.env
fi

# --- cron into ROOT's crontab: every data source these jobs touch is root-only
tmpcron="$(mktemp)"
sudo crontab -l 2>/dev/null | sed '/# A777ANCE-VOLUME-LAYER-BEGIN/,/# A777ANCE-VOLUME-LAYER-END/d' > "$tmpcron" || true
{
  echo '# A777ANCE-VOLUME-LAYER-BEGIN'
  echo '# Refresh category IP-sets every 6h; CDN IPs rotate and set elements time out at 24h.'
  printf '3 */6 * * * /usr/bin/python3 %q/populate_sets.py --apply >>/var/log/a777ance/populate-sets.log 2>&1\n' "$remote_dir"
  echo '# Collect the running month measured stats nightly. Sources /etc/a777ance/collect.env'
  echo '# if present (KUMA_KEY); without it Kuma /metrics 401s and uptime/latency stay null.'
  printf '30 0 * * * . /etc/a777ance/collect.env 2>/dev/null; /usr/bin/python3 %q/collect_stats.py --kuma-key "$KUMA_KEY" --out /var/lib/a777ance/$(date +\%%Y-\%%m).stats.json >>/var/log/a777ance/collect-stats.log 2>&1\n' "$remote_dir"
  echo '# A777ANCE-VOLUME-LAYER-END'
} >> "$tmpcron"
sudo crontab "$tmpcron"
rm -f "$tmpcron"

echo
echo '--- root crontab (tagged block) ---'
sudo crontab -l | sed -n '/# A777ANCE-VOLUME-LAYER-BEGIN/,/# A777ANCE-VOLUME-LAYER-END/p'
echo
echo '--- nftables accounting table ---'
sudo nft list table inet a777acct
echo
echo 'Counters JSON written on box: /tmp/a777ance-counters.json'
echo 'Cron logs will appear in:      /var/log/a777ance/'
REMOTE

scp -q "$runner" "$T630_HOST:$REMOTE_DIR/.deploy-runner.sh"
ssh -t "$T630_HOST" "bash '$REMOTE_DIR/.deploy-runner.sh' '$REMOTE_DIR'; rc=\$?; rm -f '$REMOTE_DIR/.deploy-runner.sh'; exit \$rc"
