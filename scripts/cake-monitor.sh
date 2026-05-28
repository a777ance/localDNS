#!/bin/bash
# Deploys to: ~/cake-monitor.sh  (chmod +x)
# Scheduled via: crontab -e  →  * * * * * /home/USERNAME/cake-monitor.sh
#
# Monitors CAKE qdisc on enp1s0. Pushes status to an Uptime Kuma Push monitor.
# Replace PUSH_URL with the token from your Push monitor (strip the query string).
#
# Uptime Kuma Push monitor setting: set Heartbeat Interval to 90s (not 60s).
# The cron fires every 60s but scheduling jitter + curl latency means the push
# can arrive at second 61-62. A 90s window absorbs that without false "down" flaps.

IFACE="enp1s0"
PUSH_URL="http://192.168.1.118:3001/api/push/<PUSH_TOKEN_CAKE>"

# Check the qdisc directly — it is the ground truth for whether CAKE is shaping.
# systemctl is-active can return inactive after daemon-reload or boot even when
# the qdisc is still applied; using it as the gate causes false "down" readings.
if tc qdisc show dev "$IFACE" | grep -q "cake"; then
    bandwidth=$(tc qdisc show dev "$IFACE" | grep -oP 'bandwidth \K[^ ]+')
    status="up"
    msg="cake_active_${bandwidth}"
else
    status="down"
    msg="cake_not_running"
fi

curl -s -G "${PUSH_URL}" \
    --data-urlencode "status=${status}" \
    --data-urlencode "msg=${msg}" > /dev/null
