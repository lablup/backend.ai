#!/usr/bin/env bash
# 14: Deployment endpoint URL is constructed and reachable.
# - Find a model card + preset (soft-skip on fresh DB)
# - Deploy with 1 replica
# - Wait until deployment.network_access.endpoint_url is populated
# - HTTP probe the URL — must return any HTTP status (i.e. URL is routable)
# - Cleanup
#
# Note: a fully-serving model image isn't guaranteed in dev clusters, so we
# only assert URL construction + L7 reachability, not 200 OK from the model.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "14_deployment_endpoint_serve"

bai_config_session
bai_login_admin

MODEL_STORE_ID="$(./bai admin project search --limit 50 2>&1 | python3 -c "
import json, sys
for it in json.load(sys.stdin).get('items', []):
    if it.get('basic_info', {}).get('name') == 'model-store':
        print(it['id']); break
")"
if [[ -z "$MODEL_STORE_ID" ]]; then
    log_error "no 'model-store' project"
    exit 1
fi

CARDS_JSON="$(./bai model-card project-search "$MODEL_STORE_ID" --limit 5 2>&1)"
CARD_ID="$(echo "$CARDS_JSON" | python3 -c "
import json,sys
items=json.load(sys.stdin).get('items',[])
print(items[0]['id'] if items else '')
")"
if [[ -z "$CARD_ID" ]]; then
    log_error "no model cards available"
    exit 1
fi
log_ok "model card: $CARD_ID"

PRESETS_JSON="$(./bai model-card available-presets "$CARD_ID" 2>&1)"
PRESET_ID="$(echo "$PRESETS_JSON" | python3 -c "
import json,sys
d=json.load(sys.stdin)
items=d.get('items') or d.get('presets') or []
print(items[0]['id'] if items else '')
")"
if [[ -z "$PRESET_ID" ]]; then
    log_error "no presets available"
    exit 1
fi

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

log_step "Deploy model card → project A"
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
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "deploy failed: $DEPLOY_OUT"; exit 1; }
log_ok "deployment: $DEPLOYMENT_ID"

cleanup() {
    log_step "Cleanup deployment"
    ./bai deployment delete "$DEPLOYMENT_ID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

log_step "Wait for endpoint_url to populate (max 90s)"
ENDPOINT_URL=""
for _ in {1..45}; do
    GET_OUT="$(./bai deployment get "$DEPLOYMENT_ID" 2>/dev/null || true)"
    URL_RAW="$(echo "$GET_OUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
na = d.get('network_access') or d.get('networkAccess') or {}
url = na.get('endpoint_url') or d.get('endpoint_url') or ''
if url and url.lower() != 'null':
    print(url)
" || true)"
    if [[ -n "$URL_RAW" ]]; then ENDPOINT_URL="$URL_RAW"; break; fi
    sleep 2
done

if [[ -z "$ENDPOINT_URL" ]]; then
    log_error "endpoint_url never populated within 90s"
    exit 1
fi
log_ok "endpoint_url: $ENDPOINT_URL"

log_step "HTTP probe endpoint (any response counts as reachable)"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$ENDPOINT_URL" || echo "000")"
if [[ "$HTTP_CODE" == "000" ]]; then
    log_error "endpoint URL not routable (curl failed)"
    exit 1
fi
log_ok "endpoint reachable (HTTP $HTTP_CODE)"

scenario_end_ok
