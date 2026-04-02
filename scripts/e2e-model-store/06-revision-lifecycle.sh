#!/bin/bash
# Scenario F: Revision lifecycle — current, search, activate
#
# Tests the new CLI commands for revision management:
#   - deployment revision current <id>
#   - deployment revision search <id>
#   - deployment revision activate <id> <rev_id>
#   - deployment update <id> <payload>
#
# Prerequisite: 03-deploy-with-preset.sh must have run (creates e2e-preset-deploy)

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

echo "=== Scenario F: Revision Lifecycle ==="

# --- Find the deployment created in scenario C ---
DEP_ID=$($BAI admin deployment search --name-contains e2e-preset-deploy 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
echo "Deployment ID: ${DEP_ID:0:8}..."

# --- 1. Get deployment (should show current_revision_id, not embedded revision) ---
echo ""
echo "--- Step 1: Get deployment ---"
DEP_RESULT=$($BAI deployment get "$DEP_ID" 2>&1)
echo "$DEP_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rev_id = data.get('current_revision_id')
print(f'  current_revision_id: {rev_id}')
# Verify no embedded revision object
assert 'revision' not in data or data.get('revision') is None, 'ERROR: revision should not be embedded'
print('  PASS: revision not embedded in deployment response')
"

# --- 2. Get current revision ---
echo ""
echo "--- Step 2: Get current revision ---"
REV_RESULT=$($BAI deployment revision current "$DEP_ID" 2>&1)
echo "$REV_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  Revision ID: {data[\"id\"][:8]}...')
print(f'  Name: {data[\"name\"]}')
print(f'  Resource slots: {data[\"resource_config\"][\"resource_slot\"]}')
print(f'  Runtime variant: {data[\"model_runtime_config\"][\"runtime_variant\"]}')
print('  PASS: current revision retrieved')
"

# --- 3. Search revisions (should have at least 1) ---
echo ""
echo "--- Step 3: Search revisions ---"
SEARCH_RESULT=$($BAI deployment revision search "$DEP_ID" 2>&1)
echo "$SEARCH_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = data.get('total_count', len(data.get('items', [])))
items = data.get('items', [])
print(f'  Total revisions: {count}')
for item in items:
    print(f'    - {item[\"name\"]} (ID: {item[\"id\"][:8]}...)')
assert count >= 1, f'ERROR: expected at least 1 revision, got {count}'
print('  PASS: revisions found')
"

# --- 4. Add a second revision ---
echo ""
echo "--- Step 4: Add second revision ---"
PRESET_ID=$($BAI admin deployment revision-preset search --name-contains e2e-vllm-4gpu 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
REV2_RESULT=$($BAI deployment revision add "$DEP_ID" "{
  \"deployment_id\": \"$DEP_ID\",
  \"revision_preset_id\": \"$PRESET_ID\",
  \"auto_activate\": false
}" 2>&1)
REV2_ID=$(echo "$REV2_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['revision']['id'])")
echo "  New revision ID: ${REV2_ID:0:8}..."

# --- 5. Search revisions again (should have 2+) ---
echo ""
echo "--- Step 5: Verify revision count ---"
SEARCH_RESULT2=$($BAI deployment revision search "$DEP_ID" 2>&1)
echo "$SEARCH_RESULT2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = data.get('total_count', len(data.get('items', [])))
assert count >= 2, f'ERROR: expected at least 2 revisions, got {count}'
print(f'  Total revisions: {count}')
print('  PASS: second revision added')
"

# --- 6. Activate the new revision ---
echo ""
echo "--- Step 6: Activate second revision ---"
ACTIVATE_RESULT=$($BAI deployment revision activate "$DEP_ID" "$REV2_ID" 2>&1)
echo "$ACTIVATE_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
activated = data.get('activated_revision_id')
print(f'  Activated revision: {activated[:8]}...' if activated else '  Activated revision: N/A')
print('  PASS: revision activated')
"

# --- 7. Verify current revision changed ---
echo ""
echo "--- Step 7: Verify current revision updated ---"
REV_AFTER=$($BAI deployment revision current "$DEP_ID" 2>&1)
echo "$REV_AFTER" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rev_id = data['id']
expected = '$REV2_ID'
assert rev_id == expected, f'ERROR: expected {expected[:8]}, got {rev_id[:8]}'
print(f'  Current revision: {rev_id[:8]}...')
print('  PASS: current revision matches activated revision')
"

# --- 8. Update deployment metadata ---
echo ""
echo "--- Step 8: Update deployment metadata ---"
UPDATE_RESULT=$($BAI deployment update "$DEP_ID" '{"desired_replica_count": 2}' 2>&1)
echo "$UPDATE_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
dep = data.get('deployment', data)
print(f'  Updated deployment: {dep[\"id\"][:8]}...')
print('  PASS: deployment updated')
"

echo ""
echo "=== Scenario F: All steps passed ==="
