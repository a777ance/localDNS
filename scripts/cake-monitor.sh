#!/bin/bash
# Deploys to: ~/cake-monitor.sh  (chmod +x)
# Scheduled via: crontab -e  →  * * * * * /home/USERNAME/cake-monitor.sh
#
# Monitors CAKE qdisc on enp1s0. Pushes status to an Uptime Kuma Push monitor.
# Replace PUSH_URL with the token from your Push monitor (strip the query string).

IFACE="enp1s0"
PUSH_URL="http://192.168.1.118:3001/api/push/<PUSH_TOKEN_CAKE>"

# Check both the systemd service and the actual qdisc
if systemctl is-active --quiet cake && tc qdisc show dev "$IFACE" | grep -q "cake"; then
    bandwidth=$(tc qdisc show dev "$IFACE" | grep -oP 'bandwidth \K[^ ]+')
    status="up"
    msg="cake active @ ${bandwidth}"
else
    status="down"
    msg="cake not running on $IFACE"
fi

curl -s "${PUSH_URL}?status=${status}&msg=${msg}" > /dev/null
