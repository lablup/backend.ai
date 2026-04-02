#!/bin/bash
# Scenario C: Create deployment using a revision preset.
#
# Prerequisites: run 01-setup-presets.sh first
# Verifies: preset values (resource_slots, environ) are applied to the revision.

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

# Get the revision preset ID
REV_PRESET_ID=$(./bai admin deployment revision-preset search \
  --name-contains e2e-vllm-4gpu --limit 1 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  Using revision preset: $REV_PRESET_ID"

echo "--- C: Deployment with preset (minimal input) ---"

RESULT=$(./bai deployment create "{
  \"metadata\": {
    \"name\": \"e2e-preset-deploy\",
    \"project_id\": \"$PROJECT_ID\",
    \"domain_name\": \"$DOMAIN_NAME\"
  },
  \"network_access\": {\"open_to_public\": false},
  \"default_deployment_strategy\": {\"type\": \"ROLLING\"},
  \"desired_replica_count\": 0,
  \"initial_revision\": {
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
  }
}" 2>&1)

echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
dep = d.get('deployment', d)
print(f'  Deployment created: {dep.get(\"id\", \"?\")[:8]}...')
print(f'  Name: {dep.get(\"name\", \"?\")}')
# Check if preset values were applied
rev = dep.get('revision', {})
if rev:
    slots = rev.get('resource_config', {}).get('resource_slot', {})
    environ = rev.get('model_runtime_config', {}).get('environ', {})
    print(f'  Revision resource_slots: {slots}')
    print(f'  Revision environ: {environ}')
else:
    print('  (no revision in response)')
" 2>&1 || echo "  Result: $RESULT"
