#!/bin/bash
# Backfill model_definition in deployment_revisions for pre-26.4.2 endpoints.
#
# Calls the admin sync-model-definitions API which reads model-definition.yaml
# from each revision's model vfolder and updates the DB.
#
# Usage:
#   ./scripts/backfill_model_definitions.sh
#
# Environment variables:
#   BACKEND_ENDPOINT  - Manager API endpoint (default: http://127.0.0.1:8091)
#   BACKEND_ACCESS_KEY - Superadmin access key
#   BACKEND_SECRET_KEY - Superadmin secret key

set -euo pipefail

ENDPOINT="${BACKEND_ENDPOINT:-http://127.0.0.1:8091}"

echo "Syncing model definitions..."
./bai admin deployment sync-model-definitions
echo "Done."
