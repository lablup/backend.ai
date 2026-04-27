#!/usr/bin/env bash
# 09: Mounted vfolder cannot be deleted; delete succeeds once session ends.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "09_vfolder_mounted_delete"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found"; exit 1; }

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-mountlock-$$"
SESSION_NAME="${SCENARIO_PREFIX}-sess-mountlock-$$"

log_step "Create vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed"; exit 1; }

PAYLOAD_FILE="$SCENARIO_TMP_DIR/enqueue-${SESSION_NAME}.json"
session_payload "$SESSION_NAME" "$IMAGE_ID" "$PROJECT_A_ID" "$VF_ID" "/home/work/${VF_NAME}" > "$PAYLOAD_FILE"

log_step "Enqueue session mounting the vfolder"
ENQ_OUT="$(./bai session enqueue "@$PAYLOAD_FILE" 2>&1)"
SESSION_ID="$(printf '%s' "$ENQ_OUT" | session_id_from)"
[[ -n "$SESSION_ID" ]] || { log_error "enqueue failed"; echo "$ENQ_OUT" >&2; exit 1; }
log_ok "session: $SESSION_ID"

log_step "Wait for session to register the mount (max 60s)"
MOUNTED_STATUS="$(wait_session_status "$SESSION_ID" 30 2 PENDING PREPARING PREPARED RUNNING || true)"
case "$MOUNTED_STATUS" in
    PENDING|PREPARING|PREPARED|RUNNING) : ;;
    TERMINATED|CANCELLED|ERROR) log_error "session ended too early ($MOUNTED_STATUS); cannot test mount lock"; exit 1 ;;
    *) log_error "session never reached mounted state (last: $MOUNTED_STATUS)"; exit 1 ;;
esac
log_ok "session at $MOUNTED_STATUS — vfolder is reserved"

# Core assertion: delete on a mounted vfolder MUST be rejected.
log_step "Attempt delete on mounted vfolder (must be rejected)"
DEL_OUT="$(./bai vfolder delete "$VF_ID" 2>&1 || true)"

STATUS_AFTER="$(./bai vfolder my-search --limit 200 2>/dev/null | VID="$VF_ID" python3 -c "
import json, sys, os
vid = os.environ['VID']
for it in json.load(sys.stdin).get('items', []):
    if it.get('id') == vid:
        print(it.get('status') or 'UNKNOWN'); sys.exit(0)
print('NOT_FOUND')
")"

case "$STATUS_AFTER" in
    delete-pending|delete-ongoing|delete-complete|delete-error|delete-aborted|NOT_FOUND)
        log_error "BUG: vfolder ${VF_ID} entered '${STATUS_AFTER}' while mounted by session ${SESSION_ID}"
        log_error "delete output: $DEL_OUT"
        terminate_session "$SESSION_ID"
        exit 1
        ;;
esac
log_ok "delete rejected — vfolder status remains '${STATUS_AFTER}'"

log_step "Terminate session and wait"
terminate_session "$SESSION_ID"
wait_session_status "$SESSION_ID" 15 2 TERMINATED CANCELLED NOT_FOUND >/dev/null || true

log_step "Delete vfolder after unmount (must succeed)"
./bai vfolder delete "$VF_ID" >/dev/null
./bai vfolder purge  "$VF_ID" >/dev/null

scenario_end_ok
