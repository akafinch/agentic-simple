#!/usr/bin/env bash
# ollama.sh — Install Ollama, configure bind address, pull model
set -euo pipefail

MODEL="${1:?Usage: ollama.sh <model_name>}"

# Install Ollama if not present
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure Ollama to listen on all interfaces (needed for VLAN/private IP access)
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

systemctl daemon-reload
systemctl enable --now ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null; then
        echo "✓ Ollama is running"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "✗ Ollama failed to start after 60 seconds"
        exit 1
    fi
    sleep 2
done

# Pull the model
echo "Pulling ${MODEL} (this may take several minutes)..."
ollama pull "${MODEL}"
echo "✓ Ollama ready: $(ollama list | grep "${MODEL}")"
