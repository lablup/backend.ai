#!/usr/bin/env bash
# 14: Deploy → endpoint URL populates → URL is L7-reachable.
# Asserts URL construction + reachability, not 200 OK from the model.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "14_deployment_endpoint_serve"

bai_config_session
bai_login_admin

MODEL_STORE_ID="$(lookup_project_id "model-store")"
[[ -n "$MODEL_STORE_ID" ]] || { log_error "no 'model-store' project"; exit 1; }

CARDS_JSON="$(./bai model-card project-search "$MODEL_STORE_ID" --limit 5 2>&1)"
CARD_ID="$(printf '%s' "$CARDS_JSON" | python3 -c "
import json, sys
items = json.load(sys.stdin).get('items', [])
print(items[0]['id'] if items else '')
")"
[[ -n "$CARD_ID" ]] || { log_error "no model cards available"; exit 1; }

PRESETS_JSON="$(./bai model-card available-presets "$CARD_ID" 2>&1)"
PRESET_ID="$(printf '%s' "$PRESETS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items') or d.get('presets') or []
print(items[0]['id'] if items else '')
")"
[[ -n "$PRESET_ID" ]] || { log_error "no presets available"; exit 1; }

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

log_step "Deploy model card → project A"
DEPLOY_OUT="$(./bai model-card deploy "$CARD_ID" \
    --project-id "$PROJECT_A_ID" \
    --revision-preset-id "$PRESET_ID" \
    --resource-group "$TEST_RESOURCE_GROUP" \
    --replicas 1 2>&1)"
DEPLOYMENT_ID="$(printf '%s' "$DEPLOY_OUT" | deployment_id_from)"
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "deploy failed: $DEPLOY_OUT"; exit 1; }
log_ok "deployment: $DEPLOYMENT_ID"

trap '{ log_step "Cleanup"; ./bai deployment delete "$DEPLOYMENT_ID" >/dev/null 2>&1 || true; }' EXIT

log_step "Wait for endpoint_url to populate (max 90s)"
ENDPOINT_URL=""
for _ in {1..45}; do
    URL_RAW="$(./bai deployment get "$DEPLOYMENT_ID" 2>/dev/null | python3 -c "
import json, sys
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
na = d.get('network_access') or d.get('networkAccess') or {}
url = na.get('endpoint_url') or d.get('endpoint_url') or ''
if url and url.lower() != 'null': print(url)
" || true)"
    if [[ -n "$URL_RAW" ]]; then ENDPOINT_URL="$URL_RAW"; break; fi
    sleep 2
done
[[ -n "$ENDPOINT_URL" ]] || { log_error "endpoint_url never populated within 90s"; exit 1; }
log_ok "endpoint_url: $ENDPOINT_URL"

log_step "HTTP probe endpoint"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$ENDPOINT_URL" || echo "000")"
[[ "$HTTP_CODE" != "000" ]] || { log_error "endpoint URL not routable (curl failed)"; exit 1; }
log_ok "endpoint reachable (HTTP $HTTP_CODE)"

scenario_end_ok
