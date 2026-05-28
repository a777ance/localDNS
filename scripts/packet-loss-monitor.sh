#!/bin/bash
# Deploys to: ~/packet-loss-monitor.sh  (chmod +x)
# Scheduled via: crontab -e  →  * * * * * /home/USERNAME/packet-loss-monitor.sh
# Packet loss monitor for Uptime Kuma (Push monitors).
# Runs every minute via cron. Pings gateway and 1.1.1.1, reports loss % and
# status to two separate Push monitors so LAN vs internet loss can be
# distinguished at a glance.
#
# Install:
#   cp scripts/packet-loss-monitor.sh ~/packet-loss-monitor.sh
#   chmod +x ~/packet-loss-monitor.sh
#   crontab -e   →   add:  * * * * * /home/USER/packet-loss-monitor.sh
#
# REPLACE the two PUSH_URL values with the tokens from your Uptime Kuma
# Push monitors (Add Monitor → Type: Push → copy the URL).
# Strip the query string — the script appends its own parameters.

ROUTER_IP="192.168.1.1"
ROUTER_PUSH_URL="http://192.168.1.118:3001/api/push/<PUSH_TOKEN_ROUTER>"
INTERNET_PUSH_URL="http://192.168.1.118:3001/api/push/<PUSH_TOKEN_INTERNET>"

# Alert if loss exceeds this %. Start at 15 while the router is being
# stabilized; lower to 5 once the hardware situation is resolved.
THRESHOLD=15

check_loss() {
  local target=$1
  local push_url=$2

  # 50 pings at 0.2s apart (~10s total). More packets = smoother loss %.
  # Each missed packet = 2% with 50 samples, vs 5% with 20 samples.
  local result
  result=$(ping -c 50 -i 0.2 -W 1 "$target" 2>/dev/null)
  local loss avg

  loss=$(echo "$result" | grep -oP '\d+(?=% packet loss)')
  avg=$(echo  "$result" | grep -oP 'rtt.*=\s*[\d.]+/\K[\d.]+' | head -1)

  loss=${loss:-100}
  avg=${avg:-0}

  if [ "$loss" -lt "$THRESHOLD" ]; then
    status="up"
  else
    status="down"
  fi

  # Put loss % in the ping field so Uptime Kuma graphs it over time.
  curl -s "${push_url}?status=${status}&msg=loss=${loss}%25&ping=${loss}" > /dev/null
}

check_loss "$ROUTER_IP"  "$ROUTER_PUSH_URL"
check_loss "1.1.1.1"     "$INTERNET_PUSH_URL"
