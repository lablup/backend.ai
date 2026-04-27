#!/usr/bin/env bash
# 15: keypair resource-policy enforces max_concurrent_sessions=1.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "15_session_concurrency_cap"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }
USER_A_ID="$(state_get user_a_id || lookup_user_id "$TEST_USER_A_EMAIL")"
[[ -n "$USER_A_ID" ]] || { log_error "user A missing"; exit 1; }

log_step "Locate user A's primary keypair + record current resource-policy"
KP_JSON="$(./bai admin keypair search --limit 200 2>/dev/null)"
USER_A_AK="$(printf '%s' "$KP_JSON" | TARGET_UID="$USER_A_ID" python3 "$SCRIPT_DIR/find_user_keypair.py")"
[[ -n "$USER_A_AK" ]] || { log_error "no active keypair for user A"; exit 1; }
ORIGINAL_POLICY="$(printf '%s' "$KP_JSON" | AK="$USER_A_AK" python3 "$SCRIPT_DIR/find_keypair_policy.py")"
log_ok "keypair $USER_A_AK (original policy: ${ORIGINAL_POLICY})"

POLICY_NAME="${SCENARIO_PREFIX}-cap1-$$"

cleanup() {
    log_step "Cleanup: restore keypair → ${ORIGINAL_POLICY}, delete temp policy"
    ./bai admin keypair update "{\"access_key\":\"${USER_A_AK}\",\"resource_policy\":\"${ORIGINAL_POLICY}\"}" >/dev/null 2>&1 || true
    ./bai admin resource-policy keypair delete "$POLICY_NAME" >/dev/null 2>&1 || true
    [[ -n "${SESS1_ID:-}" ]] && terminate_session "$SESS1_ID"
    [[ -n "${SESS2_ID:-}" ]] && terminate_session "$SESS2_ID"
}
trap cleanup EXIT

log_step "Create temp policy '${POLICY_NAME}' (max_concurrent_sessions=1)"
./bai admin resource-policy keypair create \
    --name "$POLICY_NAME" \
    --default-for-unspecified UNLIMITED \
    --max-concurrent-sessions 1 \
    --max-containers-per-session 1 \
    --idle-timeout 3600 \
    --max-concurrent-sftp-sessions 1 \
    --total-resource-slots '[{"resource_type":"cpu","quantity":"100"},{"resource_type":"mem","quantity":"107374182400"}]' \
    --allowed-vfolder-hosts '[{"host":"local:volume1","permissions":["create-vfolder","modify-vfolder","delete-vfolder","mount-in-session","upload-file","download-file","invite-others","set-user-specific-permission"]}]' >/dev/null

log_step "Reassign user A's keypair to '${POLICY_NAME}'"
./bai admin keypair update "{\"access_key\":\"${USER_A_AK}\",\"resource_policy\":\"${POLICY_NAME}\"}" >/dev/null

# Re-login as user A so the new policy applies to subsequent calls.
bai_login_user_a
bai_login_admin
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found"; exit 1; }
bai_login_user_a

S1_NAME="${SCENARIO_PREFIX}-cap-s1-$$"
S2_NAME="${SCENARIO_PREFIX}-cap-s2-$$"
P1="$SCENARIO_TMP_DIR/${S1_NAME}.json"
P2="$SCENARIO_TMP_DIR/${S2_NAME}.json"
session_payload "$S1_NAME" "$IMAGE_ID" "$PROJECT_A_ID" > "$P1"
session_payload "$S2_NAME" "$IMAGE_ID" "$PROJECT_A_ID" > "$P2"

log_step "Enqueue session #1 (should succeed and hold the slot)"
ENQ1="$(./bai session enqueue "@$P1" 2>&1)"
SESS1_ID="$(printf '%s' "$ENQ1" | session_id_from)"
[[ -n "$SESS1_ID" ]] || { log_error "session #1 enqueue failed"; echo "$ENQ1" >&2; exit 1; }
log_ok "session #1: $SESS1_ID"

# Even PENDING/PREPARING consumes the slot — no need to wait for RUNNING.
sleep 2

log_step "Enqueue session #2 — MUST be rejected by max_concurrent_sessions=1"
if ENQ2="$(./bai session enqueue "@$P2" 2>&1)"; then
    if echo "$ENQ2" | grep -qiE "concurrent|quota|policy|exceed|limit"; then
        log_ok "session #2 rejected (response indicates limit)"
    else
        SESS2_ID="$(printf '%s' "$ENQ2" | session_id_from || true)"
        log_error "BUG: session #2 enqueue succeeded under max_concurrent_sessions=1"
        log_error "response: $(echo "$ENQ2" | head -c 500)"
        exit 1
    fi
else
    log_ok "session #2 rejected (CLI exit non-zero)"
fi

log_step "Verify only one session is active for user A"
ACTIVE_COUNT="$(./bai my session search --limit 200 2>/dev/null | python3 "$SCRIPT_DIR/count_active_sessions.py")"
[[ "$ACTIVE_COUNT" -le 1 ]] || { log_error "more than one active session ($ACTIVE_COUNT)"; exit 1; }
log_ok "concurrency limit enforced (active=$ACTIVE_COUNT)"

scenario_end_ok
