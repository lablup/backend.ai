#!/bin/bash
# Scenario G: Route health lifecycle — provisioning → running/healthy
#
# Tests that a deployment with serve.py + model_definition preset
# transitions through: provisioning → running/not_checked → running/healthy
#
# Prerequisite: 01-setup-presets.sh must have run (creates e2e-cpu-healthcheck preset)

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

echo "=== Scenario G: Route Health Lifecycle ==="

# Find CPU preset
CPU_PRESET_ID=$($BAI admin deployment revision-preset search --name-contains e2e-cpu-healthcheck 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "  CPU preset: $CPU_PRESET_ID"

# --- 1. Create deployment with replica=1 ---
echo ""
echo "--- Step 1: Create deployment with replica=1 ---"
DEP_RESULT=$($BAI deployment create \
  --name e2e-route-health \
  --project-id "$PROJECT_ID" \
  --desired-replicas 1 \
  --initial-revision "{
    \"revision_preset_id\": \"$CPU_PRESET_ID\",
    \"cluster_config\": {\"mode\": \"SINGLE_NODE\", \"size\": 1},
    \"resource_config\": {\"resource_group\": {\"name\": \"default\"}, \"resource_slots\": {\"entries\": []}, \"resource_opts\": null},
    \"image\": {\"id\": \"$IMAGE_ID\"},
    \"model_runtime_config\": {\"runtime_variant\": \"custom\"},
    \"model_mount_config\": {\"vfolder_id\": \"$MODEL_VFOLDER_ID\", \"mount_destination\": \"/models\", \"definition_path\": \"\"},
    \"auto_activate\": true
  }" 2>&1)
DEP_ID=$(echo "$DEP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['deployment']['id'])")
echo "  Deployment: $DEP_ID"

# --- 2. Wait for route to become healthy ---
echo ""
echo "--- Step 2: Waiting for route health (max 60s) ---"
for i in $(seq 1 12); do
  sleep 5
  ROUTE_INFO=$($PY -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:develove@localhost:8101/backend')
    async with engine.begin() as conn:
        r = await conn.execute(sa.text(\"SELECT status, health_status FROM routings WHERE endpoint = '$DEP_ID'::uuid LIMIT 1\"))
        row = r.fetchone()
        if row:
            print(f'{row.status}|{row.health_status}')
        else:
            print('none|none')
asyncio.run(main())
" 2>&1)
  STATUS=$(echo "$ROUTE_INFO" | cut -d'|' -f1)
  HEALTH=$(echo "$ROUTE_INFO" | cut -d'|' -f2)
  echo "  [$((i*5))s] status=$STATUS health=$HEALTH"
  if [ "$HEALTH" = "healthy" ]; then
    echo "  Route is HEALTHY!"
    break
  fi
done

# --- 3. Check route history ---
echo ""
echo "--- Step 3: Route history ---"
$PY -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:develove@localhost:8101/backend')
    async with engine.begin() as conn:
        r = await conn.execute(sa.text('''
            SELECT category, phase, from_status, to_status, from_health_status, to_health_status, result, attempts
            FROM route_history WHERE deployment_id = '$DEP_ID'::uuid ORDER BY created_at
        '''))
        for row in r:
            print(f'  [{row.category}] {row.phase}: status={row.from_status}->{row.to_status} health={row.from_health_status}->{row.to_health_status} result={row.result} x{row.attempts}')
asyncio.run(main())
" 2>&1

# --- 4. Check via CLI ---
echo ""
echo "--- Step 4: Verify via CLI ---"
$BAI deployment get "$DEP_ID" 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  deployment status: {d[\"metadata\"][\"status\"]}')
print(f'  current_revision_id: {d[\"current_revision_id\"]}')
"
$BAI admin deployment replica search --deployment-id "$DEP_ID" 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
for item in d['items']:
    print(f'  replica: readiness={item[\"readiness_status\"]} liveness={item[\"liveness_status\"]}')
"

# --- 5. Cleanup ---
echo ""
echo "--- Step 5: Cleanup ---"
$BAI deployment delete "$DEP_ID" 2>&1 | python3 -c "import sys,json; print(f'  Deleted: {json.load(sys.stdin)[\"id\"]}')"

echo ""
echo "=== Scenario G complete ==="
