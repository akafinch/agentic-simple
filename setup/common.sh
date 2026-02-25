#!/usr/bin/env bash
# common.sh — OS packages, NVIDIA driver check, Docker, Node.js
set -euo pipefail

echo "── Installing base packages ──"
apt-get update && apt-get upgrade -y
apt-get install -y \
    curl jq net-tools \
    docker.io docker-compose-v2 \
    python3 python3-pip python3-venv build-essential

systemctl enable --now docker

# Node.js 20 LTS (needed on orchestrator for frontend build)
if [ "${ROLE:-}" = "orchestrator" ]; then
    if ! command -v node &>/dev/null; then
        echo "Installing Node.js 20 LTS..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    fi
    echo "✓ Node.js $(node --version)"
fi

# NVIDIA drivers — only install if not already working
if ! command -v nvidia-smi &>/dev/null || ! nvidia-smi &>/dev/null; then
    echo "Installing NVIDIA drivers..."
    apt-get install -y nvidia-driver-550 nvidia-cuda-toolkit
    echo "⚠️  Reboot required. Run 'sudo reboot' then re-run 'make setup'."
    exit 1
else
    echo "✓ GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
fi

echo "✓ Base setup complete"
