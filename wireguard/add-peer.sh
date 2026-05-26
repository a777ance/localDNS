#!/bin/bash
set -euo pipefail

# Add a new WireGuard peer without restarting the tunnel or dropping existing connections.
# Usage: sudo bash wireguard/add-peer.sh <name>
#
# Assigns the next available IP in 10.8.0.0/24, generates a keypair, writes the
# client config to /etc/wireguard/peers/<name>.conf, and prints a QR code.

[[ $EUID -ne 0 ]] && { echo "Run as root."; exit 1; }
[[ $# -lt 1 ]] && { echo "Usage: $0 <peer-name>"; exit 1; }

NAME="$1"
WG_CONF="/etc/wireguard/wg0.conf"
PEERS_DIR="/etc/wireguard/peers"
CLIENT_CONF="${PEERS_DIR}/${NAME}.conf"
WG_PORT="51820"
SERVER_WG_IP="10.8.0.1"

[[ ! -f "$WG_CONF" ]] && { echo "$WG_CONF not found. Run wireguard/setup.sh first."; exit 1; }

# Auto-assign next unused address in 10.8.0.0/24 (skips .1 = server, starts at .2)
USED=$(grep -oP '10\.8\.0\.\K\d+' "$WG_CONF" || true)
NEXT=2
while echo "$USED" | grep -qx "$NEXT" 2>/dev/null; do ((NEXT++)); done
CLIENT_IP="10.8.0.${NEXT}"

# Derive server public key from the private key already in wg0.conf
SERVER_PRIVATE=$(awk '/^\[Interface\]/{f=1} f && /^PrivateKey/{print $3; exit}' "$WG_CONF")
SERVER_PUBLIC=$(echo "$SERVER_PRIVATE" | wg pubkey)

PUBLIC_IP=$(curl -s --max-time 10 ifconfig.me) || PUBLIC_IP="YOUR_PUBLIC_IP"

# Generate client keypair
CLIENT_PRIVATE=$(wg genkey)
CLIENT_PUBLIC=$(echo "$CLIENT_PRIVATE" | wg pubkey)

umask 077
mkdir -p "$PEERS_DIR"

cat > "$CLIENT_CONF" <<EOF
[Interface]
PrivateKey = ${CLIENT_PRIVATE}
Address    = ${CLIENT_IP}/32
DNS        = ${SERVER_WG_IP}

[Peer]
PublicKey           = ${SERVER_PUBLIC}
Endpoint            = ${PUBLIC_IP}:${WG_PORT}
AllowedIPs          = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
EOF

# Append peer to server config
cat >> "$WG_CONF" <<EOF

[Peer]
# ${NAME}
PublicKey  = ${CLIENT_PUBLIC}
AllowedIPs = ${CLIENT_IP}/32
EOF

# Apply live — no tunnel restart, existing peers unaffected
wg set wg0 peer "$CLIENT_PUBLIC" allowed-ips "${CLIENT_IP}/32"
wg-quick save wg0

echo
echo "=== Peer '${NAME}' added at ${CLIENT_IP} ==="
echo
echo "=== Client config: ${CLIENT_CONF} ==="
cat "$CLIENT_CONF"
echo
echo "=== Scan with WireGuard app ==="
qrencode -t ansiutf8 < "$CLIENT_CONF"
echo
wg show wg0
