#!/bin/bash
set -euo pipefail
LAN="192.168.0.0/16"
WG="10.8.0.0/24"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw default deny routed
# LAN services
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
# WireGuard: listen port open to Anywhere (phone connects from cellular)
ufw allow in to any port 51820 proto udp
# WireGuard tunnel clients: allow DNS so the phone reaches Pi-hole at 10.8.0.1
ufw allow in from "$WG" to any port 53 proto tcp
ufw allow in from "$WG" to any port 53 proto udp
ufw allow out to any port 53 proto udp
ufw --force enable
ufw status verbose
