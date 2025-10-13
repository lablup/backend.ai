#!/bin/bash
set -e

# Compose GraphQL Router Execution Config
# Run this script from project root whenever GraphQL subgraph schemas are modified

echo "Composing GraphQL router execution config..."

npx wgc@latest router compose \
  -i configs/graphql/cosmo-graph.yaml \
  -o configs/graphql/router-config.json

echo ""
echo "✓ Router config successfully generated!"
echo "  Restart the router: docker compose -f docker-compose.halfstack-main.yml restart backendai-half-apollo-router"
