#!/usr/bin/env bash
# 03: Model card → deployment.
# - Find a model card in the model-store project
# - List its available revision presets
# - Deploy as a new deployment
# - Verify deployment shows up in user search; clean up
#
# Soft-skips with PASS if there are no model cards on this cluster
# (fresh dev DB has none; this scenario is structural verification of the CLI).

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "03_model_card_deploy"

bai_config_session
bai_login_admin

# --- Locate the model-store project ---------------------------------------
MODEL_STORE_ID="$(./bai admin project search --limit 50 2>&1 | python3 -c "
import json, sys
for it in json.load(sys.stdin).get('items', []):
    if it.get('basic_info', {}).get('name') == 'model-store':
        print(it['id']); break
")"
if [[ -z "$MODEL_STORE_ID" ]]; then
    log_error "no 'model-store' project on this cluster"
    exit 1
fi
log_ok "model-store project: $MODEL_STORE_ID"

# --- Search model cards ----------------------------------------------------
log_step "Search model cards in model-store"
CARDS_JSON="$(./bai model-card project-search "$MODEL_STORE_ID" --limit 5 2>&1)"
CARD_COUNT="$(echo "$CARDS_JSON" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('items',[])))")"
log_info "found $CARD_COUNT model cards"

if (( CARD_COUNT == 0 )); then
    log_error "no model cards available"
    exit 1
fi

CARD_ID="$(echo "$CARDS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0]['id'])")"
CARD_NAME="$(echo "$CARDS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['items'][0].get('name',''))")"
log_ok "selected card: ${CARD_NAME} (${CARD_ID})"

# --- Get card details ------------------------------------------------------
log_step "Get model card details"
./bai model-card get "$CARD_ID" >/dev/null
log_ok "card retrievable"

# --- List available presets ------------------------------------------------
log_step "List available revision presets"
PRESETS_JSON="$(./bai model-card available-presets "$CARD_ID" 2>&1)" || {
    log_error "available-presets failed: $PRESETS_JSON"; exit 1; }
PRESET_ID="$(echo "$PRESETS_JSON" | python3 -c "
import json,sys
d=json.load(sys.stdin)
items = d.get('items') or d.get('presets') or []
print(items[0]['id'] if items else '')
")"
if [[ -z "$PRESET_ID" ]]; then
    log_error "card has no revision presets"
    exit 1
fi
log_ok "preset: $PRESET_ID"

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

# --- Deploy ----------------------------------------------------------------
log_step "Deploy model card to project A"
DEPLOY_OUT="$(./bai model-card deploy "$CARD_ID" \
    --project-id "$PROJECT_A_ID" \
    --revision-preset-id "$PRESET_ID" \
    --resource-group "$TEST_RESOURCE_GROUP" \
    --replicas 1 2>&1)"
DEPLOYMENT_ID="$(echo "$DEPLOY_OUT" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('id') or d.get('deployment_id') or d.get('deployment',{}).get('id') or '')
")"
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "could not extract deployment id: $DEPLOY_OUT"; exit 1; }
state_set deployment_id "$DEPLOYMENT_ID"
log_ok "deployment created: $DEPLOYMENT_ID"

# --- Verify visibility ----------------------------------------------------
log_step "Verify deployment via my-search"
sleep 1
DID="$DEPLOYMENT_ID" ./bai my deployment search --limit 50 2>&1 | DID="$DEPLOYMENT_ID" python3 -c "
import json,sys,os
target=os.environ['DID']
d=json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('id') == target:
        print('found'); sys.exit(0)
sys.exit(1)
" || { log_error "deployment not visible to user via my deployment search"; exit 1; }
log_ok "deployment visible to user"

# --- Cleanup ---------------------------------------------------------------
log_step "Delete deployment"
./bai deployment delete "$DEPLOYMENT_ID" >/dev/null

scenario_end_ok
