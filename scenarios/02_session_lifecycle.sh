#!/usr/bin/env bash
# 02: Compute session lifecycle — vfolder + interactive session + terminate.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "02_session_lifecycle"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found: $TEST_IMAGE_NAME"; exit 1; }

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-session-$$"
log_step "Create mount-target vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder create lookup failed"; exit 1; }
state_set session_vf_id "$VF_ID"

SESSION_NAME="${SCENARIO_PREFIX}-sess-$$"
PAYLOAD_FILE="$SCENARIO_TMP_DIR/enqueue-${SESSION_NAME}.json"
session_payload "$SESSION_NAME" "$IMAGE_ID" "$PROJECT_A_ID" "$VF_ID" "/home/work/${VF_NAME}" > "$PAYLOAD_FILE"

log_step "Enqueue session '${SESSION_NAME}' (mounting ${VF_NAME})"
ENQ_OUT="$(./bai session enqueue "@$PAYLOAD_FILE" 2>&1)"
SESSION_ID="$(printf '%s' "$ENQ_OUT" | session_id_from)"
[[ -n "$SESSION_ID" ]] || { log_error "Failed to extract session id"; echo "$ENQ_OUT" | head -c 2000 >&2; exit 1; }
state_set session_id "$SESSION_ID"
log_ok "session: $SESSION_ID"

log_step "Wait for session to appear in my-search"
wait_session_status "$SESSION_ID" 20 1 \
    PENDING PREPARING PREPARED RUNNING TERMINATED CANCELLED ERROR >/dev/null \
    || { log_error "session never appeared in my-search"; exit 1; }

log_step "Wait for session to settle (max 60s)"
FINAL_STATUS="$(wait_session_status "$SESSION_ID" 30 2 RUNNING TERMINATED CANCELLED ERROR || true)"
log_info "session settled at: ${FINAL_STATUS:-(unknown after timeout)}"

log_step "Terminate session"
terminate_session "$SESSION_ID"

log_step "Verify session terminated within 30s"
wait_session_status "$SESSION_ID" 15 2 TERMINATED CANCELLED NOT_FOUND >/dev/null \
    || log_warn "session did not reach TERMINATED within timeout"

log_step "Cleanup mount vfolder"
./bai vfolder delete "$VF_ID" >/dev/null || true
./bai vfolder purge "$VF_ID" >/dev/null || true

scenario_end_ok
