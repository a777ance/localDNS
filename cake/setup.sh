#!/bin/bash
# Deploys to: /usr/local/sbin/cake-setup.sh  (chmod 755)
# Managed by: systemd/cake.service
# Apply CAKE queueing discipline on enp1s0 egress.
#
# Scope: upload path only — traffic leaving the t630 toward the router/internet.
# This covers upload bufferbloat for WireGuard VPN clients (the t630 is in
# the forwarding path for all WireGuard traffic).
#
# Does NOT fix download bufferbloat for general LAN devices. The Netgear R7000
# is the right fix point for that: DD-WRT/FreshTomato both support CAKE/fq_codel
# and the R7000 is a well-supported target. See network-context.md for detail.
#
# Install:
#   sudo cp cake/setup.sh /usr/local/sbin/cake-setup.sh
#   sudo chmod 755 /usr/local/sbin/cake-setup.sh
#   sudo cp systemd/cake.service /etc/systemd/system/
#   sudo systemctl daemon-reload && sudo systemctl enable --now cake
#
# Idempotent — safe to re-run.

set -euo pipefail

IFACE="${1:-enp1s0}"

# 90% of measured ISP upload (94.3 Mbps on Wi-Fi through VPN → raw WAN ~98–100 Mbps).
# Must be BELOW the ISP ceiling so CAKE's queue fills before the modem's unmanaged
# FIFO — that's what keeps latency flat under load.
# Verify: tc -s qdisc show dev enp1s0 — "drop" counter increments under sustained
# upload load, confirming CAKE is the bottleneck, not the modem.
# Adjust here if your line speed changes, then redeploy: sudo bash cake/setup.sh
UPLOAD_MBPS=85

# Remove any existing root qdisc so this script is idempotent.
tc qdisc del dev "$IFACE" root 2>/dev/null || true

# Apply CAKE.
#
# bandwidth   hard cap below ISP upload — OS queue becomes bottleneck before modem
# nat         conntrack transparency: CAKE sees real flow IPs behind WireGuard's
#             MASQUERADE, so iPhone (10.8.0.2) and laptop (10.8.0.3) get separate
#             fair-queue slots instead of being lumped as one flow
# diffserv4   4-tier DSCP scheduling: bulk < best-effort < video < voice+DNS
#             Pi-hole/Unbound DNS responses get highest priority automatically
# wash        zero DSCP markings before egress — don't leak internal markings to ISP
# split-gso   split GSO super-packets before queuing so CAKE's latency guarantees
#             apply to individual packets, not 64 KB batches
tc qdisc add dev "$IFACE" root cake \
    bandwidth "${UPLOAD_MBPS}mbit" \
    nat \
    diffserv4 \
    wash \
    split-gso

echo "CAKE active on $IFACE egress @ ${UPLOAD_MBPS} Mbit/s"
tc qdisc show dev "$IFACE"
