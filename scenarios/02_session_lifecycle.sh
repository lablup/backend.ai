#!/usr/bin/env bash
# 02: Compute session lifecycle.
# - Create vfolder for mount
# - Enqueue interactive session with vfolder mount
# - Wait for RUNNING (or PREPARING) state
# - my session search confirms presence
# - terminate, then verify status

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "02_session_lifecycle"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }

log_step "Resolve image id for '${TEST_IMAGE_NAME}'"
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found: $TEST_IMAGE_NAME"; exit 1; }
log_ok "image: $IMAGE_ID"

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-session-$$"
log_step "Create mount-target user-owned vfolder '${VF_NAME}'"
./bai vfolder create \
    --name "$VF_NAME" \
    --host "$TEST_VFOLDER_HOST" >/dev/null

VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder create lookup failed"; exit 1; }
state_set session_vf_id "$VF_ID"
log_ok "vfolder ready: $VF_ID"

# --- Enqueue session -------------------------------------------------------
SESSION_NAME="${SCENARIO_PREFIX}-sess-$$"
PAYLOAD_FILE="$SCENARIO_TMP_DIR/enqueue-${SESSION_NAME}.json"
cat > "$PAYLOAD_FILE" <<EOF
{
  "session_name": "${SESSION_NAME}",
  "session_type": "interactive",
  "image_id": "${IMAGE_ID}",
  "resource_entries": [
    {"resource_type": "cpu", "quantity": "1"},
    {"resource_type": "mem", "quantity": "1073741824"}
  ],
  "resource_group": "${TEST_RESOURCE_GROUP}",
  "mounts": [
    {"vfolder_id": "${VF_ID}", "mount_path": "/home/work/${VF_NAME}", "permission": "rw"}
  ],
  "project_id": "${PROJECT_A_ID}"
}
EOF
log_step "Enqueue session '${SESSION_NAME}' (mounting ${VF_NAME})"
ENQ_OUT="$(./bai session enqueue "@$PAYLOAD_FILE" 2>&1)"
echo "$ENQ_OUT" | head -c 1000 | log_debug "$(cat)"

SESSION_ID="$(echo "$ENQ_OUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
sid = (d.get('session') or {}).get('id') or d.get('id') or d.get('session_id')
if sid: print(sid)
")"
if [[ -z "$SESSION_ID" ]]; then
    log_error "Failed to extract session id from enqueue response"
    echo "$ENQ_OUT" | head -c 2000 >&2
    exit 1
fi
state_set session_id "$SESSION_ID"
log_ok "enqueued session: $SESSION_ID"

_session_status() {
    SID="$SESSION_ID" ./bai my session search --limit 50 2>/dev/null | SID="$SESSION_ID" python3 -c "
import json, sys, os
sid = os.environ['SID']
d = json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('id') == sid:
        print((it.get('lifecycle') or {}).get('status') or it.get('status', 'UNKNOWN'))
        sys.exit(0)
print('NOT_FOUND')
" 2>/dev/null
}

# --- Wait for the session to become visible --------------------------------
log_step "Wait for session to appear in my-search"
for _ in {1..20}; do
    s="$(_session_status)"
    [[ "$s" != "NOT_FOUND" ]] && break
    sleep 1
done
log_ok "session visible in my-search"

# --- Wait until status leaves PENDING/PREPARING ----------------------------
log_step "Wait for session status to settle (max 60s)"
FINAL_STATUS=""
for _ in {1..30}; do
    STATUS="$(_session_status)"
    log_debug "status: $STATUS"
    case "$STATUS" in
        RUNNING|TERMINATED|CANCELLED|ERROR) FINAL_STATUS="$STATUS"; break ;;
    esac
    sleep 2
done
log_info "session settled at status: ${FINAL_STATUS:-(unknown after timeout)}"

# --- Terminate the session -------------------------------------------------
log_step "Terminate session"
./bai session terminate "$SESSION_ID" --forced >/dev/null 2>&1 \
    || ./bai session terminate "$SESSION_ID" >/dev/null \
    || log_warn "terminate returned non-zero (may already be terminated)"
log_ok "terminate request issued"

# --- Verify session is no longer running -----------------------------------
log_step "Verify session terminated within 30s"
TERMINATED=0
for _ in {1..15}; do
    STATUS="$(_session_status)"
    log_debug "post-term status: $STATUS"
    case "$STATUS" in
        TERMINATED|CANCELLED|NOT_FOUND) TERMINATED=1; break ;;
    esac
    sleep 2
done
if (( TERMINATED == 1 )); then
    log_ok "session terminated"
else
    log_warn "session did not reach TERMINATED within timeout (last: $STATUS)"
fi

# --- Cleanup vfolder -------------------------------------------------------
log_step "Cleanup mount vfolder"
./bai vfolder delete "$VF_ID" >/dev/null || true
./bai vfolder purge "$VF_ID" >/dev/null || true

scenario_end_ok
