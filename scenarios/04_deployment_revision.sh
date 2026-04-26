#!/usr/bin/env bash
# 04: Deployment + revision management.
# - Create a bare deployment without an initial revision (CLI supports this)
# - List revisions (expect zero)
# - Update deployment metadata
# - Delete deployment
#
# Adding a revision requires a complete revision config (cluster_config,
# resource_config, image, model_runtime_config, model_mount_config) which
# is normally built from a model card preset. We skip the add path on the
# bare deployment but verify the listing/update/delete CRUD path here.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "04_deployment_revision"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }

bai_login_user_a

DEP_NAME="${SCENARIO_PREFIX}-dep-$$"
log_step "Create bare deployment '${DEP_NAME}' (no initial revision)"
DEPLOY_OUT="$(./bai deployment create \
    --name "$DEP_NAME" \
    --project-id "$PROJECT_A_ID" \
    --domain-name "$TEST_DOMAIN" \
    --desired-replicas 0 \
    --strategy ROLLING 2>&1)"
DEPLOYMENT_ID="$(echo "$DEPLOY_OUT" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('id') or d.get('deployment',{}).get('id') or d.get('deployment_id') or '')
")"
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "could not parse deployment id from: $DEPLOY_OUT"; exit 1; }
state_set bare_deployment_id "$DEPLOYMENT_ID"
log_ok "deployment id: $DEPLOYMENT_ID"

# --- Get + project-search verify ------------------------------------------
log_step "Get deployment by id"
./bai deployment get "$DEPLOYMENT_ID" >/dev/null
log_ok "GET works"

log_step "project-search lists deployment"
DID="$DEPLOYMENT_ID" ./bai deployment project-search "$PROJECT_A_ID" --limit 50 2>&1 | DID="$DEPLOYMENT_ID" python3 -c "
import json, sys, os
target=os.environ['DID']
d=json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('id') == target: sys.exit(0)
sys.exit(1)
"
log_ok "deployment present in project-search"

# --- Revision list (expect none on bare deployment) ------------------------
log_step "List revisions (expect 0 for bare deployment)"
REVS_JSON="$(./bai deployment revision search "$DEPLOYMENT_ID" --limit 10 2>&1)"
COUNT="$(echo "$REVS_JSON" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin); print(len(d.get('items',[])))
except Exception:
    print('?')
")"
log_info "revision count: $COUNT"

# --- current revision (should be empty/null) -------------------------------
log_step "current-revision on bare deployment (informational)"
./bai deployment revision current "$DEPLOYMENT_ID" 2>&1 | head -c 300 | log_debug "$(cat)" || true

# --- Update metadata -------------------------------------------------------
log_step "Update deployment metadata via CLI"
./bai deployment update --help 2>&1 | head -30 | log_debug "$(cat)"
UPDATE_OUT="$(./bai deployment update "$DEPLOYMENT_ID" --desired-replicas 0 2>&1)" \
    || { log_error "deployment update failed: $UPDATE_OUT"; exit 1; }
log_ok "deployment update succeeded"

# --- Delete ----------------------------------------------------------------
log_step "Delete deployment"
./bai deployment delete "$DEPLOYMENT_ID" >/dev/null
log_ok "deployment deleted"

# --- Verify status is terminal after delete --------------------------------
# Note: deployment delete is a soft-delete — the row stays visible with a
# terminal status. We assert the status is one of the terminal states.
sleep 1
log_step "Verify deployment status is terminal after delete"
DID="$DEPLOYMENT_ID" ./bai deployment project-search "$PROJECT_A_ID" --limit 50 2>&1 | DID="$DEPLOYMENT_ID" python3 -c "
import json, sys, os
target=os.environ['DID']
TERM={'STOPPED','DESTROYED','DELETED','TERMINATED','CANCELLED'}
d=json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('id') == target:
        st=(it.get('lifecycle') or {}).get('status') or it.get('status') or ''
        if st in TERM:
            print(f'terminal: {st}'); sys.exit(0)
        print(f'NOT TERMINAL: {st}'); sys.exit(1)
print('absent (also acceptable)'); sys.exit(0)
" || { log_error "deployment delete did not produce terminal status"; exit 1; }
log_ok "deployment in terminal state after delete"

scenario_end_ok
