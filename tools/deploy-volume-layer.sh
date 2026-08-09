#!/usr/bin/env bash
# Deploy and verify the nftables per-category volume layer on the live t630.
#
# Usage:
#   T630_HOST=USER@192.168.1.118 T630_USER=USER tools/deploy-volume-layer.sh
#   T630_HOST=USER@10.8.0.1      T630_USER=USER tools/deploy-volume-layer.sh
#
# This implements DEPLOY-QUEUE Stage 10: copy collect/, validate/load nftables,
# populate the sets, install tagged cron entries, and print verification counters.
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

ssh "$T630_HOST" bash -s -- "$REMOTE_DIR" <<'REMOTE'
set -euo pipefail
remote_dir="$1"
cd "$remote_dir"

sudo nft -c -f nftables-accounting.nft
sudo nft -f nftables-accounting.nft
python3 populate_sets.py >/tmp/a777ance-populate-sets.nft
test -s /tmp/a777ance-populate-sets.nft
sudo python3 populate_sets.py --apply
sudo nft -j list counters table inet a777acct >/tmp/a777ance-counters.json
sudo install -d -m 755 /var/lib/a777ance

tmpcron="$(mktemp)"
crontab -l 2>/dev/null | sed '/# A777ANCE-VOLUME-LAYER-BEGIN/,/# A777ANCE-VOLUME-LAYER-END/d' > "$tmpcron" || true
{
  echo '# A777ANCE-VOLUME-LAYER-BEGIN'
  echo '# Refresh category IP-sets every 6h; CDN IPs rotate and set elements time out.'
  printf '3 */6 * * * /usr/bin/python3 %q/populate_sets.py --apply >/dev/null 2>&1\n' "$remote_dir"
  echo '# Collect the running month measured stats nightly.'
  printf '30 0 * * * /usr/bin/python3 %q/collect_stats.py --out /var/lib/a777ance/$(date +\%%Y-\%%m).stats.json >/dev/null 2>&1\n' "$remote_dir"
  echo '# A777ANCE-VOLUME-LAYER-END'
} >> "$tmpcron"
crontab "$tmpcron"
rm -f "$tmpcron"

crontab -l | sed -n '/# A777ANCE-VOLUME-LAYER-BEGIN/,/# A777ANCE-VOLUME-LAYER-END/p'
sudo nft list table inet a777acct
echo 'Counters JSON written on box: /tmp/a777ance-counters.json'
REMOTE
