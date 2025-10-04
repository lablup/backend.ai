#!/bin/bash
set -e

echo "=== Backend.AI Manager Container starting ==="

# fixtures directory creation (default path structure)
mkdir -p /app/fixtures/manager

# RPC keypair not found. Generating...
if [ ! -f "/app/fixtures/manager/manager.key" ] || [ ! -f "/app/fixtures/manager/manager.key_secret" ]; then
    echo "RPC keypair not found. Generating..."
    python -m ai.backend.manager.cli generate-rpc-keypair /app/fixtures/manager 'manager'
    echo "RPC keypair generated successfully."
    echo "   - Public Key: /app/fixtures/manager/manager.key"
    echo "   - Secret Key: /app/fixtures/manager/manager.key_secret"
else
    echo "RPC keypair already exists."
fi

# Log directory creation
mkdir -p /var/log/backend.ai

# IPC directory creation
mkdir -p /tmp/backend.ai/ipc

echo "=== Manager server starting ==="
exec python -m ai.backend.manager.server --config /etc/backend.ai/manager.toml
