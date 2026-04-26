#!/usr/bin/env bash
# 09: Mounted vfolder cannot be deleted.
# - User A creates a vfolder
# - Enqueues a session that mounts the vfolder
# - Waits until session is at least PREPARING (mount is reserved)
# - Attempts `vfolder delete` → MUST fail (mount holds it)
# - Terminates session, waits for TERMINATED
# - `vfolder delete` MUST succeed once nothing holds the mount

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "09_vfolder_mounted_delete"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }

log_step "Resolve image id for '${TEST_IMAGE_NAME}'"
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found: $TEST_IMAGE_NAME"; exit 1; }

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-mountlock-$$"
SESSION_NAME="${SCENARIO_PREFIX}-sess-mountlock-$$"

log_step "Create vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed"; exit 1; }
log_ok "vfolder: $VF_ID"

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

log_step "Enqueue session mounting the vfolder"
ENQ_OUT="$(./bai session enqueue "@$PAYLOAD_FILE" 2>&1)"
SESSION_ID="$(echo "$ENQ_OUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
sid = (d.get('session') or {}).get('id') or d.get('id') or d.get('session_id')
if sid: print(sid)
")"
[[ -n "$SESSION_ID" ]] || { log_error "enqueue failed"; echo "$ENQ_OUT" >&2; exit 1; }
log_ok "session enqueued: $SESSION_ID"

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

# Wait until session is past initial enqueue — any of {PENDING, PREPARING,
# PREPARED, RUNNING} means the manager has registered the mount.
log_step "Wait for session to register the mount (max 60s)"
MOUNTED_STATUS=""
for _ in {1..30}; do
    s="$(_session_status)"
    log_debug "status: $s"
    case "$s" in
        PENDING|PREPARING|PREPARED|RUNNING) MOUNTED_STATUS="$s"; break ;;
        TERMINATED|CANCELLED|ERROR) log_error "session ended too early ($s); cannot test mount lock"; exit 1 ;;
    esac
    sleep 2
done
[[ -n "$MOUNTED_STATUS" ]] || { log_error "session never reached mounted state"; exit 1; }
log_ok "session at $MOUNTED_STATUS — vfolder is reserved"

# --- Core assertion: delete on a mounted vfolder MUST fail -----------------
log_step "Attempt delete on mounted vfolder (must be rejected)"
DEL_OUT="$(./bai vfolder delete "$VF_ID" 2>&1 || true)"
DEL_EXIT="$?"
log_debug "delete output: $(echo "$DEL_OUT" | head -c 500)"

# Verify the vfolder is still NOT in a deleted state.
STATUS_AFTER="$(./bai vfolder my-search --limit 200 2>/dev/null | VID="$VF_ID" python3 -c "
import json, sys, os
vid = os.environ['VID']
d = json.load(sys.stdin)
for it in d.get('items', []):
    if it.get('id') == vid:
        print(it.get('status') or 'UNKNOWN')
        sys.exit(0)
print('NOT_FOUND')
")"
log_debug "vfolder status after delete attempt: $STATUS_AFTER"

DELETED_STATES="delete-pending delete-ongoing delete-complete delete-error delete-aborted NOT_FOUND"
IS_DELETED=0
for s in $DELETED_STATES; do
    [[ "$STATUS_AFTER" == "$s" ]] && IS_DELETED=1
done

if (( IS_DELETED == 1 )); then
    log_error "BUG: vfolder ${VF_ID} entered '${STATUS_AFTER}' while still mounted by session ${SESSION_ID}"
    log_error "delete output: $DEL_OUT"
    # Best-effort cleanup before exiting
    ./bai session terminate "$SESSION_ID" --forced >/dev/null 2>&1 || true
    exit 1
fi
log_ok "delete rejected — vfolder status remains '${STATUS_AFTER}'"

# --- Terminate session, then delete should now work ------------------------
log_step "Terminate session"
./bai session terminate "$SESSION_ID" --forced >/dev/null 2>&1 \
    || ./bai session terminate "$SESSION_ID" >/dev/null \
    || log_warn "terminate returned non-zero"

log_step "Wait for session TERMINATED (max 30s)"
for _ in {1..15}; do
    s="$(_session_status)"
    case "$s" in
        TERMINATED|CANCELLED|NOT_FOUND) break ;;
    esac
    sleep 2
done

log_step "Delete vfolder after session ended (must succeed)"
./bai vfolder delete "$VF_ID" >/dev/null
./bai vfolder purge  "$VF_ID" >/dev/null
log_ok "vfolder deleted after unmount"

scenario_end_ok
