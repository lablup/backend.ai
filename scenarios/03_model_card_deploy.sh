#!/usr/bin/env bash
# 03: Model card → deployment via `model-card deploy` happy path.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "03_model_card_deploy"

bai_config_session
bai_login_admin

MODEL_STORE_ID="$(lookup_project_id "model-store")"
[[ -n "$MODEL_STORE_ID" ]] || { log_error "no 'model-store' project on this cluster"; exit 1; }

log_step "Search model cards in model-store"
CARDS_JSON="$(./bai model-card project-search "$MODEL_STORE_ID" --limit 5 2>&1)"
CARD_ID="$(printf '%s' "$CARDS_JSON" | python3 -c "
import json, sys
items = json.load(sys.stdin).get('items', [])
print(items[0]['id'] if items else '')
")"
[[ -n "$CARD_ID" ]] || { log_error "no model cards available"; exit 1; }
log_ok "card: $CARD_ID"

./bai model-card get "$CARD_ID" >/dev/null

log_step "List available revision presets"
PRESETS_JSON="$(./bai model-card available-presets "$CARD_ID" 2>&1)" \
    || { log_error "available-presets failed: $PRESETS_JSON"; exit 1; }
PRESET_ID="$(printf '%s' "$PRESETS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items') or d.get('presets') or []
print(items[0]['id'] if items else '')
")"
[[ -n "$PRESET_ID" ]] || { log_error "card has no revision presets"; exit 1; }

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

log_step "Deploy model card to project A"
DEPLOY_OUT="$(./bai model-card deploy "$CARD_ID" \
    --project-id "$PROJECT_A_ID" \
    --revision-preset-id "$PRESET_ID" \
    --resource-group "$TEST_RESOURCE_GROUP" \
    --replicas 1 2>&1)"
DEPLOYMENT_ID="$(printf '%s' "$DEPLOY_OUT" | deployment_id_from)"
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "could not extract deployment id: $DEPLOY_OUT"; exit 1; }
state_set deployment_id "$DEPLOYMENT_ID"
log_ok "deployment: $DEPLOYMENT_ID"

log_step "Verify deployment via my deployment search"
sleep 1
DID="$DEPLOYMENT_ID" ./bai my deployment search --limit 50 2>&1 | DID="$DEPLOYMENT_ID" python3 -c "
import json, sys, os
target = os.environ['DID']
for it in json.load(sys.stdin).get('items', []):
    if it.get('id') == target: sys.exit(0)
sys.exit(1)
" || { log_error "deployment not visible via my deployment search"; exit 1; }

log_step "Delete deployment"
./bai deployment delete "$DEPLOYMENT_ID" >/dev/null

scenario_end_ok
