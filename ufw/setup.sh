#!/bin/bash
# Run directly on the t630: sudo bash ufw/setup.sh
# Resets and rebuilds all firewall rules from scratch. Safe to re-run.
# All services LAN-only (192.168.0.0/16) except 51820/UDP (WireGuard, open to Anywhere).
# WG subnet (10.8.0.0/24) also allowed for DNS, SSH, and Uptime Kuma
# because full-tunnel peers source from 10.8.0.x, not 192.168.x.x.
set -euo pipefail
LAN="192.168.0.0/16"
WG="10.8.0.0/24"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw default allow routed  # required for WireGuard to forward peer traffic out enp1s0
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
# WireGuard tunnel clients: allow SSH and Kuma so they're reachable when full
# tunnel is active (all traffic exits via WG; source IP is 10.8.0.x not 192.168.x.x)
ufw allow in from "$WG" to any port 22 proto tcp
ufw allow in from "$WG" to any port 3001 proto tcp
ufw allow out to any port 53 proto udp
ufw --force enable
ufw status verbose
