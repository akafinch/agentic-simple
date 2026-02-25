#!/usr/bin/env bash
# vlan.sh — Configure VLAN IP via Netplan on eth1
set -euo pipefail

VLAN_IP="${1:?Usage: vlan.sh <ip_address>}"

# Check that eth1 exists (requires VLAN attachment + reboot in Cloud Manager)
if ! ip link show eth1 &>/dev/null; then
    echo "✗ eth1 not found."
    echo "  VLAN interface only appears after:"
    echo "    1. Attaching VLAN in Linode Cloud Manager → VM → Configurations → Edit"
    echo "    2. Rebooting the VM"
    echo "  See docs/vlan-setup.md for step-by-step instructions."
    exit 1
fi

# Write Netplan config
cat > /etc/netplan/60-vlan.yaml <<EOF
network:
  version: 2
  ethernets:
    eth1:
      addresses:
        - ${VLAN_IP}/24
EOF

netplan apply

echo "✓ VLAN configured: $(ip -4 addr show eth1 | grep inet)"
