#!/usr/bin/env bash
set -euo pipefail

RECREATE=0

usage() {
  cat <<'USAGE'
Usage: refresh-graphql-gateway.sh [-r|--recreate]

Regenerates the GraphQL schema, copies it to the project root and reloads the
Apollo Router (Hive Gateway).

  -r, --recreate  Recreate the gateway container instead of restarting it.
                  Required when supergraph.graphql or gateway.config.ts changed:
                  they are mounted as docker configs, which are materialized at
                  container creation time, so a restart keeps the old content.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    -r|--recreate)
      RECREATE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "==> 1. Regenerating GraphQL schema..."
./scripts/generate-graphql-schema.sh

echo "==> 2. Copying schema and gateway config to project root..."
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
cp configs/graphql/gateway.config.ts ./gateway.config.ts

if [ $RECREATE -eq 1 ]; then
  echo "==> 3. Recreating Apollo Router..."
  docker compose -f docker-compose.halfstack.current.yml up -d --force-recreate --wait backendai-half-apollo-router
else
  echo "==> 3. Restarting Apollo Router..."
  docker compose -f docker-compose.halfstack.current.yml restart backendai-half-apollo-router
  echo "    NOTE: the schema and gateway config are docker configs; pass --recreate to apply their updates."
fi
echo "==> Done!"
