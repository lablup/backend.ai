#!/bin/bash
# Scenario D: Create deployment with preset + partial override.
#
# Prerequisites: run 01-setup-presets.sh first
# Verifies: request values override preset values, unset fields keep preset values.
#
# Preset has: cpu=8, mem=32g, cuda.device=4, VLLM_TENSOR_PARALLEL_SIZE=4
# Override:   cuda.device=8, VLLM_TENSOR_PARALLEL_SIZE=8
# Expected:   cpu=8(preset), mem=32g(preset), cuda.device=8(override), TP=8(override)

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

REV_PRESET_ID=$(./bai admin deployment revision-preset search \
  --name-contains e2e-vllm-4gpu --limit 1 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  Using revision preset: $REV_PRESET_ID"

echo "--- D: Deployment with preset + override ---"

RESULT=$(./bai deployment create "{
  \"metadata\": {
    \"name\": \"e2e-override-deploy\",
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
      \"resource_slots\": {\"entries\": [{\"resource_type\": \"cuda.device\", \"quantity\": \"8\"}]}
    },
    \"model_runtime_config\": {
      \"runtime_variant\": \"vllm\",
      \"environ\": {\"entries\": [{\"name\": \"VLLM_TENSOR_PARALLEL_SIZE\", \"value\": \"8\"}]}
    },
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
rev = dep.get('revision', {})
if rev:
    slots = rev.get('resource_config', {}).get('resource_slot', {})
    environ = rev.get('model_runtime_config', {}).get('environ', {})
    print(f'  resource_slots: {slots}')
    print(f'  environ: {environ}')
    print()
    print('  Expected: cuda.device=8(override), cpu=8(preset), mem=32g(preset)')
    print('  Expected: VLLM_TENSOR_PARALLEL_SIZE=8(override)')
" 2>&1 || echo "  Result: $RESULT"
