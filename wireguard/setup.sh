#!/bin/bash
set -euo pipefail

# Full-tunnel WireGuard VPN server for the HP t630.
# Run as root. Generates server + iOS client keys, writes /etc/wireguard/wg0.conf,
# enables ip forwarding, starts wg-quick@wg0, and prints a QR code for the iOS app.
# Safe to re-run — prompts before overwriting existing config.

WAN_IFACE="enp1s0"
WG_PORT="51820"
SERVER_WG_IP="10.8.0.1"
CLIENT_WG_IP="10.8.0.2"
WG_SUBNET="10.8.0.0/24"
WG_CONF="/etc/wireguard/wg0.conf"
CLIENT_CONF="/etc/wireguard/ios-client.conf"

[[ $EUID -ne 0 ]] && { echo "Run as root."; exit 1; }

if [[ -f "$WG_CONF" ]]; then
    read -rp "$WG_CONF already exists. Regenerate all keys? [y/N] " yn
    [[ "${yn,,}" != "y" ]] && { echo "Aborted."; exit 0; }
    systemctl stop wg-quick@wg0 2>/dev/null || true
fi

apt-get install -y --quiet wireguard-tools qrencode

umask 077
mkdir -p /etc/wireguard

SERVER_PRIVATE=$(wg genkey)
SERVER_PUBLIC=$(echo "$SERVER_PRIVATE" | wg pubkey)
CLIENT_PRIVATE=$(wg genkey)
CLIENT_PUBLIC=$(echo "$CLIENT_PRIVATE" | wg pubkey)

PUBLIC_IP=$(curl -s --max-time 10 ifconfig.me) || PUBLIC_IP="YOUR_PUBLIC_IP"

cat > "$WG_CONF" <<EOF
[Interface]
Address    = ${SERVER_WG_IP}/24
ListenPort = ${WG_PORT}
PrivateKey = ${SERVER_PRIVATE}
PostUp   = iptables -t nat -A POSTROUTING -s ${WG_SUBNET} -o ${WAN_IFACE} -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -s ${WG_SUBNET} -o ${WAN_IFACE} -j MASQUERADE

[Peer]
# iPhone
PublicKey  = ${CLIENT_PUBLIC}
AllowedIPs = ${CLIENT_WG_IP}/32
EOF

cat > "$CLIENT_CONF" <<EOF
[Interface]
PrivateKey = ${CLIENT_PRIVATE}
Address    = ${CLIENT_WG_IP}/32
DNS        = ${SERVER_WG_IP}

[Peer]
PublicKey           = ${SERVER_PUBLIC}
Endpoint            = ${PUBLIC_IP}:${WG_PORT}
AllowedIPs          = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
EOF

# Persist IP forwarding across reboots
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

systemctl enable --now wg-quick@wg0

echo
echo "=== Server public key ==="
echo "$SERVER_PUBLIC"
echo
echo "=== iOS client config ($CLIENT_CONF) ==="
cat "$CLIENT_CONF"
echo
echo "=== Scan with WireGuard iOS app ==="
qrencode -t ansiutf8 < "$CLIENT_CONF"
echo
wg show wg0
