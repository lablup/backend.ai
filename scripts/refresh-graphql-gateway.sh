#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "==> 1. Regenerating GraphQL schema..."
./scripts/generate-graphql-schema.sh

echo "==> 2. Copying schema and gateway config to project root..."
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
cp configs/graphql/gateway.config.ts ./gateway.config.ts

read -rp "==> 3. Restart Apollo Router? [y/N] " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
  docker compose -f docker-compose.halfstack.current.yml restart backendai-half-apollo-router
  echo "==> Done!"
else
  echo "==> Skipped Apollo Router restart."
fi
