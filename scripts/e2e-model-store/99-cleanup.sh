#!/bin/bash
# Cleanup: remove all E2E test resources.
#
# Deletes deployments, revision presets, and variant presets created by the E2E tests.

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

echo "--- Cleanup: Deployments ---"
for name in e2e-manual-deploy e2e-preset-deploy e2e-override-deploy e2e-route-health; do
  DEP_ID=$(./bai admin deployment search --name-contains "$name" --limit 1 2>&1 \
    | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(items[0]['id'] if items else '')" 2>/dev/null)
  if [ -n "$DEP_ID" ]; then
    ./bai deployment delete "$DEP_ID" 2>&1 | python3 -c "import sys,json; print(f'  Deleted deployment: {json.load(sys.stdin)}')" 2>/dev/null || echo "  Failed to delete $name"
  fi
done

echo "--- Cleanup: Deployment revision presets ---"
for name in e2e-vllm-4gpu e2e-cpu-healthcheck; do
  PRESET_ID=$(./bai admin deployment revision-preset search --name-contains "$name" --limit 1 2>&1 \
    | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(items[0]['id'] if items else '')" 2>/dev/null)
  if [ -n "$PRESET_ID" ]; then
    ./bai admin deployment revision-preset delete "$PRESET_ID" 2>&1 | python3 -c "import sys,json; print(f'  Deleted revision preset: {json.load(sys.stdin)}')" 2>/dev/null || echo "  Failed to delete $name"
  fi
done

echo "--- Cleanup: Runtime variant presets ---"
for name in e2e-tensor-parallel-size e2e-gpu-memory-utilization; do
  PRESET_ID=$(./bai admin runtime-variant-preset search --name-contains "$name" --limit 1 2>&1 \
    | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; print(items[0]['id'] if items else '')" 2>/dev/null)
  if [ -n "$PRESET_ID" ]; then
    ./bai admin runtime-variant-preset delete "$PRESET_ID" 2>&1 | python3 -c "import sys,json; print(f'  Deleted variant preset: {json.load(sys.stdin)}')" 2>/dev/null || echo "  Failed to delete $name"
  fi
done

echo "--- Cleanup complete ---"
