#!/usr/bin/env bash
# firewall.sh — UFW rules per role (orchestrator or specialist)
set -euo pipefail

ROLE="${1:?Usage: firewall.sh <orchestrator|specialist>}"

echo "Configuring firewall for role: ${ROLE}"

ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# SSH — always allowed
ufw allow 22/tcp

# Ollama — accessible from private network only
ufw allow from 10.0.0.0/24 to any port 11434 proto tcp

if [ "$ROLE" = "orchestrator" ]; then
    # FastAPI serves both API and built frontend on port 8000
    ufw allow 8000/tcp
fi

ufw --force enable

echo "✓ Firewall configured for: ${ROLE}"
ufw status verbose
