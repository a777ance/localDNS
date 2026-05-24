#!/bin/bash
set -euo pipefail
LAN="192.168.0.0/16"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw default deny routed
ufw allow in from "$LAN" to any port 53 proto tcp
ufw allow in from "$LAN" to any port 53 proto udp
ufw allow in from "$LAN" to any port 5335 proto tcp
ufw allow in from "$LAN" to any port 5335 proto udp
ufw allow in from "$LAN" to any port 22 proto tcp
ufw allow in from "$LAN" to any port 8080 proto tcp
ufw allow in from "$LAN" to any port 3389 proto tcp
ufw allow in from "$LAN" to any port 4000 proto tcp
ufw allow in from "$LAN" to any port 4000 proto udp
ufw allow in from "$LAN" to any port 5353 proto udp
ufw allow in from "$LAN" to any port 3001 proto tcp
ufw allow out to any port 53 proto udp
ufw --force enable
ufw status verbose
