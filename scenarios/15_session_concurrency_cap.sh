#!/usr/bin/env bash
# 15: keypair resource-policy enforces max_concurrent_sessions.
# - Create a temp keypair resource policy with max_concurrent_sessions=1
# - Reassign user A's keypair to the temp policy
# - Enqueue session #1 (interactive, holds the slot)
# - Try to enqueue session #2 — MUST fail
# - Restore: delete sessions, restore keypair policy, delete temp policy

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "15_session_concurrency_cap"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }
USER_A_ID="$(state_get user_a_id || lookup_user_id "$TEST_USER_A_EMAIL")"
[[ -n "$USER_A_ID" ]] || { log_error "user A missing"; exit 1; }

# Pick a keypair owned by user A (active, not main bootstrap key).
log_step "Locate user A's primary keypair"
USER_A_AK="$(./bai admin keypair search --limit 200 2>/dev/null | TARGET_UID="$USER_A_ID" python3 -c "
import json, sys, os
uid = os.environ['TARGET_UID']
d = json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('user_id') == uid and it.get('is_active'):
        print(it['access_key']); break
")"
[[ -n "$USER_A_AK" ]] || { log_error "no active keypair for user A"; exit 1; }
ORIGINAL_POLICY="$(./bai admin keypair search --limit 200 2>/dev/null | AK="$USER_A_AK" python3 -c "
import json, sys, os
ak = os.environ['AK']
d = json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('access_key') == ak:
        print(it.get('resource_policy') or 'default'); break
")"
log_ok "keypair $USER_A_AK (current policy: ${ORIGINAL_POLICY})"

POLICY_NAME="${SCENARIO_PREFIX}-cap1-$$"

cleanup() {
    log_step "Cleanup: restore keypair → ${ORIGINAL_POLICY}, delete policy"
    ./bai admin keypair update "{\"access_key\":\"${USER_A_AK}\",\"resource_policy\":\"${ORIGINAL_POLICY}\"}" >/dev/null 2>&1 || true
    ./bai admin resource-policy keypair delete "$POLICY_NAME" >/dev/null 2>&1 || true
    if [[ -n "${SESS1_ID:-}" ]]; then
        ./bai session terminate "$SESS1_ID" --forced >/dev/null 2>&1 || true
    fi
    if [[ -n "${SESS2_ID:-}" ]]; then
        ./bai session terminate "$SESS2_ID" --forced >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

log_step "Create temp policy '${POLICY_NAME}' with max_concurrent_sessions=1"
./bai admin resource-policy keypair create \
    --name "$POLICY_NAME" \
    --default-for-unspecified UNLIMITED \
    --max-concurrent-sessions 1 \
    --max-containers-per-session 1 \
    --idle-timeout 3600 \
    --max-concurrent-sftp-sessions 1 \
    --total-resource-slots '[{"resource_type":"cpu","quantity":"100"},{"resource_type":"mem","quantity":"107374182400"}]' \
    --allowed-vfolder-hosts '[{"host":"local:volume1","permissions":["create-vfolder","modify-vfolder","delete-vfolder","mount-in-session","upload-file","download-file","invite-others","set-user-specific-permission"]}]' >/dev/null
log_ok "policy created"

log_step "Reassign user A's keypair to '${POLICY_NAME}'"
./bai admin keypair update "{\"access_key\":\"${USER_A_AK}\",\"resource_policy\":\"${POLICY_NAME}\"}" >/dev/null
log_ok "keypair updated"

# Re-login as user A so the new policy is applied to subsequent calls.
bai_login_user_a

log_step "Resolve image id"
bai_login_admin
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found"; exit 1; }
bai_login_user_a

_payload() {
    local name="$1"
    cat <<EOF
{
  "session_name": "${name}",
  "session_type": "interactive",
  "image_id": "${IMAGE_ID}",
  "resource_entries": [
    {"resource_type": "cpu", "quantity": "1"},
    {"resource_type": "mem", "quantity": "1073741824"}
  ],
  "resource_group": "${TEST_RESOURCE_GROUP}",
  "project_id": "${PROJECT_A_ID}"
}
EOF
}

S1_NAME="${SCENARIO_PREFIX}-cap-s1-$$"
S2_NAME="${SCENARIO_PREFIX}-cap-s2-$$"
P1="$SCENARIO_TMP_DIR/${S1_NAME}.json"
P2="$SCENARIO_TMP_DIR/${S2_NAME}.json"
_payload "$S1_NAME" > "$P1"
_payload "$S2_NAME" > "$P2"

log_step "Enqueue session #1 (should succeed and hold the slot)"
ENQ1="$(./bai session enqueue "@$P1" 2>&1)"
SESS1_ID="$(echo "$ENQ1" | python3 -c "
import json, sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(1)
sid=(d.get('session') or {}).get('id') or d.get('id') or d.get('session_id')
if sid: print(sid)
")"
[[ -n "$SESS1_ID" ]] || { log_error "session #1 enqueue failed"; echo "$ENQ1" >&2; exit 1; }
log_ok "session #1: $SESS1_ID"

# Don't wait for RUNNING — even the PENDING/PREPARING entry consumes the slot.
sleep 2

log_step "Enqueue session #2 — MUST be rejected by max_concurrent_sessions=1"
if ENQ2="$(./bai session enqueue "@$P2" 2>&1)"; then
    # Manager sometimes accepts the enqueue but rejects later — check explicit error
    if echo "$ENQ2" | grep -qiE "concurrent|quota|policy|exceed|limit"; then
        log_ok "session #2 rejected (response indicates limit)"
    else
        SESS2_ID="$(echo "$ENQ2" | python3 -c "
import json, sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
sid=(d.get('session') or {}).get('id') or d.get('id') or d.get('session_id')
if sid: print(sid)
")"
        log_error "BUG: session #2 enqueue succeeded under max_concurrent_sessions=1"
        log_error "response: $(echo "$ENQ2" | head -c 500)"
        exit 1
    fi
else
    log_ok "session #2 rejected (CLI exit non-zero)"
fi

log_step "Verify only one session is active for user A"
ACTIVE_COUNT="$(./bai my session search --limit 200 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
TERM = {'TERMINATED','CANCELLED','ERROR'}
n = 0
for it in d.get('items', []):
    s = (it.get('lifecycle') or {}).get('status') or it.get('status','')
    if s and s not in TERM:
        n += 1
print(n)
")"
log_info "active sessions: $ACTIVE_COUNT"
[[ "$ACTIVE_COUNT" -le 1 ]] || { log_error "more than one active session ($ACTIVE_COUNT)"; exit 1; }
log_ok "concurrency limit enforced"

scenario_end_ok
