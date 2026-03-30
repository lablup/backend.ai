#!/bin/sh

set -e

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
cd "$BASE_PATH"

echo "Generating GraphQL v1 schema..."
./backend.ai mgr api dump-gql-schema --output docs/manager/graphql-reference/schema.graphql

echo "Generating GraphQL v2 schema..."
./backend.ai mgr api dump-gql-schema --v2 --output docs/manager/graphql-reference/v2-schema.graphql

echo "Generating supergraph..."
./backend.ai mgr api generate-supergraph --config configs/graphql/supergraph.yaml -o docs/manager/graphql-reference

echo "GraphQL schema generation completed successfully."
