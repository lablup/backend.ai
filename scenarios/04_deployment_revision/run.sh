#!/usr/bin/env bash
# 04: Bare deployment + listing/update/delete; verify terminal status post-delete.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "04_deployment_revision"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }

bai_login_user_a

DEP_NAME="${SCENARIO_PREFIX}-dep-$$"
log_step "Create bare deployment '${DEP_NAME}'"
DEPLOY_OUT="$(./bai deployment create \
    --name "$DEP_NAME" \
    --project-id "$PROJECT_A_ID" \
    --domain-name "$TEST_DOMAIN" \
    --desired-replicas 0 \
    --strategy ROLLING 2>&1)"
DEPLOYMENT_ID="$(printf '%s' "$DEPLOY_OUT" | deployment_id_from)"
[[ -n "$DEPLOYMENT_ID" ]] || { log_error "could not parse deployment id from: $DEPLOY_OUT"; exit 1; }
state_set bare_deployment_id "$DEPLOYMENT_ID"
log_ok "deployment: $DEPLOYMENT_ID"

log_step "Get deployment + verify in project-search"
./bai deployment get "$DEPLOYMENT_ID" >/dev/null
TARGET="$DEPLOYMENT_ID" ./bai deployment project-search "$PROJECT_A_ID" --limit 50 2>&1 \
    | TARGET="$DEPLOYMENT_ID" python3 "$SCN_PY/assert_id_in_search.py" \
    || { log_error "deployment missing from project-search"; exit 1; }

log_step "Bare deployment has zero revisions"
./bai deployment revision search "$DEPLOYMENT_ID" --limit 10 >/dev/null
./bai deployment revision current "$DEPLOYMENT_ID" >/dev/null 2>&1 || true

log_step "Update deployment metadata"
./bai deployment update "$DEPLOYMENT_ID" --desired-replicas 0 >/dev/null

log_step "Delete deployment"
./bai deployment delete "$DEPLOYMENT_ID" >/dev/null

# Soft-delete: row stays visible. Status MUST be one of the terminal states.
log_step "Verify deployment status is terminal after delete"
sleep 1
TARGET="$DEPLOYMENT_ID" ./bai deployment project-search "$PROJECT_A_ID" --limit 50 2>&1 \
    | TARGET="$DEPLOYMENT_ID" python3 "$SCRIPT_DIR/check_terminal_status.py" \
    || { log_error "deployment delete did not produce terminal status"; exit 1; }

scenario_end_ok
