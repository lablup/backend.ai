#!/bin/bash
# Scenario B: Create deployment with all values specified manually (no preset).
#
# Prerequisites: source 00-env.sh
# Verifies: existing flow works without preset.

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

echo "--- B: Manual deployment (no preset) ---"

RESULT=$(./bai deployment create "{
  \"metadata\": {
    \"name\": \"e2e-manual-deploy\",
    \"project_id\": \"$PROJECT_ID\",
    \"domain_name\": \"$DOMAIN_NAME\"
  },
  \"network_access\": {\"open_to_public\": false},
  \"default_deployment_strategy\": {\"type\": \"ROLLING\"},
  \"desired_replica_count\": 0,
  \"initial_revision\": {
    \"image\": {\"id\": \"$IMAGE_ID\"},
    \"cluster_config\": {\"mode\": \"SINGLE_NODE\", \"size\": 1},
    \"resource_config\": {
      \"resource_group\": \"$RESOURCE_GROUP\",
      \"resource_slots\": {\"entries\": [{\"resource_type\": \"cpu\", \"quantity\": \"2\"}, {\"resource_type\": \"mem\", \"quantity\": \"4g\"}]}
    },
    \"model_runtime_config\": {\"runtime_variant\": \"custom\"},
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
print(f'  Status: {dep.get(\"status\", \"?\")}')
" 2>&1 || echo "  Result: $RESULT"
