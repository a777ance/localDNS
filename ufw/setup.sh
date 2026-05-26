#!/bin/bash
set -euo pipefail
LAN="192.168.0.0/16"
VPN="10.8.0.0/24"   # WireGuard tunnel subnet
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
ufw allow out to any port 53 proto udp
# WireGuard — the one port open to the internet; traffic is authenticated by public-key crypto
ufw allow 51820/udp
# DNS for VPN clients (Pi-hole via WireGuard interface)
ufw allow in from "$VPN" to any port 53 proto tcp
ufw allow in from "$VPN" to any port 53 proto udp
# Allow VPN clients to route through to the internet (MASQUERADE applied by wg0 PostUp)
ufw route allow in on wg0 out on enp1s0
ufw --force enable
ufw status verbose
