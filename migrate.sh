#!/usr/bin/env bash
set -euo pipefail

echo "=== localDNS 2.0 Lossless Migration Engine ==="

# Detect repository root
if [ ! -d ".git" ] && [ ! -f "README.md" ]; then
    echo "Error: This script must be executed from the root of the localDNS repository."
    exit 1
fi

# Create backup
BACKUP_DIR="../localDNS_backup_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup to ${BACKUP_DIR}..."
mkdir -p "$BACKUP_DIR"
cp -r ./* "$BACKUP_DIR/"

# Define directory structure
declare -A DIRECTORIES=(
    ["01-core-network"]="01-core-network/unbound 01-core-network/pihole 01-core-network/host-dns 01-core-network/ufw 01-core-network/wireguard"
    ["02-performance"]="02-performance/cake 02-performance/gpu-performance"
    ["03-monitoring"]="03-monitoring/uptime-kuma 03-monitoring/monitors"
    ["04-user-services"]="04-user-services/remote-desktop 04-user-services/ai-orchestration 04-user-services/console"
)

echo "Creating consolidated folders..."
for cat in "${!DIRECTORIES[@]}"; do
    for subdir in ${DIRECTORIES[$cat]}; do
        mkdir -p "$subdir"
    done
done

move_files() {
    local src_dir="$1"
    local dest_dir="$2"
    if [ -d "$src_dir" ]; then
        echo "  -> Moving ${src_dir} to ${dest_dir}"
        cp -r "$src_dir"/* "$dest_dir/"
    fi
}

# Migrate configurations losslessly
move_files "01-unbound" "01-core-network/unbound"
move_files "02-pihole" "01-core-network/pihole"
move_files "03-host-dns" "01-core-network/host-dns"
move_files "04-ufw" "01-core-network/ufw"
move_files "05-wireguard" "01-core-network/wireguard"
move_files "06-cake" "02-performance/cake"
move_files "08-gpu-performance" "02-performance/gpu-performance"
move_files "07-uptime-kuma" "03-monitoring/uptime-kuma"

# Move monitors
if [ -f "03-monitoring/uptime-kuma/packet-loss-monitor.sh" ]; then
    mv "03-monitoring/uptime-kuma/packet-loss-monitor.sh" "03-monitoring/monitors/"
fi
if [ -f "03-monitoring/uptime-kuma/cake-monitor.sh" ]; then
    mv "03-monitoring/uptime-kuma/cake-monitor.sh" "03-monitoring/monitors/"
fi

move_files "09-remote-desktop" "04-user-services/remote-desktop"
move_files "10-ai-orchestration" "04-user-services/ai-orchestration"
move_files "11-console" "04-user-services/console"

# Rewrite paths in configurations and scripts
update_references() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        sed -i 's|01-unbound/|01-core-network/unbound/|g' "$file_path" 2>/dev/null || true
        sed -i 's|02-pihole/|01-core-network/pihole/|g' "$file_path" 2>/dev/null || true
        sed -i 's|03-host-dns/|01-core-network/host-dns/|g' "$file_path" 2>/dev/null || true
        sed -i 's|04-ufw/|01-core-network/ufw/|g' "$file_path" 2>/dev/null || true
        sed -i 's|05-wireguard/|01-core-network/wireguard/|g' "$file_path" 2>/dev/null || true
        sed -i 's|06-cake/|02-performance/cake/|g' "$file_path" 2>/dev/null || true
        sed -i 's|07-uptime-kuma/|03-monitoring/|g' "$file_path" 2>/dev/null || true
        sed -i 's|08-gpu-performance/|02-performance/gpu-performance/|g' "$file_path" 2>/dev/null || true
        sed -i 's|09-remote-desktop/|04-user-services/remote-desktop/|g' "$file_path" 2>/dev/null || true
        sed -i 's|10-ai-orchestration/|04-user-services/ai-orchestration/|g' "$file_path" 2>/dev/null || true
        sed -i 's|11-console/|04-user-services/console/|g' "$file_path" 2>/dev/null || true
    fi
}

echo "Rewriting path references..."
find 01-core-network 02-performance 03-monitoring 04-user-services -type f | while read -r file; do
    update_references "$file"
done

# Prune legacy folders
echo "Pruning legacy folders..."
LEGACY_DIRS=("01-unbound" "02-pihole" "03-host-dns" "04-ufw" "05-wireguard" "06-cake" "07-uptime-kuma" "08-gpu-performance" "09-remote-desktop" "10-ai-orchestration" "11-console")
for dir in "${LEGACY_DIRS[@]}"; do
    rm -rf "$dir"
done

echo "=== MIGRATION COMPLETE ==="
