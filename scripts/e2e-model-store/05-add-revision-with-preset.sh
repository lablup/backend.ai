#!/bin/bash
# Scenario E: Add a new revision to an existing deployment using a preset.
#
# Prerequisites: run 03-deploy-with-preset.sh first (creates e2e-preset-deploy)
# Verifies: add_revision with revision_preset_id applies preset values.

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

# Find the deployment created in scenario C
DEPLOYMENT_ID=$(./bai admin deployment search --name-contains e2e-preset-deploy --limit 1 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  Deployment: $DEPLOYMENT_ID"

REV_PRESET_ID=$(./bai admin deployment revision-preset search \
  --name-contains e2e-vllm-4gpu --limit 1 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  Using revision preset: $REV_PRESET_ID"

echo "--- E: Add revision with preset ---"

RESULT=$(./bai deployment revision add "$DEPLOYMENT_ID" "{
  \"revision_preset_id\": \"$REV_PRESET_ID\",
  \"image\": {\"id\": \"$IMAGE_ID\"},
  \"cluster_config\": {\"mode\": \"SINGLE_NODE\", \"size\": 1},
  \"resource_config\": {
    \"resource_group\": \"$RESOURCE_GROUP\",
    \"resource_slots\": {\"entries\": []}
  },
  \"model_runtime_config\": {\"runtime_variant\": \"vllm\"},
  \"model_mount_config\": {
    \"vfolder_id\": \"$MODEL_VFOLDER_ID\",
    \"definition_path\": \"model-definition.yaml\",
    \"mount_destination\": \"/models\"
  }
}" 2>&1)

echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
rev = d.get('revision', d)
print(f'  Revision added: {rev.get(\"id\", \"?\")[:8]}...')
print(f'  Name: {rev.get(\"name\", \"?\")}')
" 2>&1 || echo "  Result: $RESULT"

echo ""
echo "--- Listing revisions ---"
./bai admin deployment revision search --deployment-id "$DEPLOYMENT_ID" 2>&1 \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Total revisions: {d[\"total_count\"]}')
for item in d['items']:
    print(f'    - {item[\"id\"][:8]}... {item.get(\"name\", \"?\")}')
" 2>&1 || true
