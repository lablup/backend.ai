#!/usr/bin/env bash
# 13: BATCH session prints marker; `session logs` retrieves it after exit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "13_session_exec_logs"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }
IMAGE_ID="$(lookup_image_id "$TEST_IMAGE_NAME")"
[[ -n "$IMAGE_ID" ]] || { log_error "image not found"; exit 1; }

bai_login_user_a

MARKER="hello-scenario-${RANDOM}-${RANDOM}"
SESSION_NAME="${SCENARIO_PREFIX}-sess-batch-$$"
PAYLOAD_FILE="$SCENARIO_TMP_DIR/enqueue-${SESSION_NAME}.json"

cat > "$PAYLOAD_FILE" <<EOF
{
  "session_name": "${SESSION_NAME}",
  "session_type": "batch",
  "image_id": "${IMAGE_ID}",
  "resource_entries": [
    {"resource_type": "cpu", "quantity": "1"},
    {"resource_type": "mem", "quantity": "1073741824"}
  ],
  "resource_group": "${TEST_RESOURCE_GROUP}",
  "project_id": "${PROJECT_A_ID}",
  "batch": {"startup_command": "echo ${MARKER}"}
}
EOF

log_step "Enqueue BATCH session with marker output"
ENQ_OUT="$(./bai session enqueue "@$PAYLOAD_FILE" 2>&1)"
SESSION_ID="$(printf '%s' "$ENQ_OUT" | session_id_from)"
[[ -n "$SESSION_ID" ]] || { log_error "enqueue failed"; echo "$ENQ_OUT" >&2; exit 1; }
log_ok "session: $SESSION_ID"

log_step "Wait for BATCH session to TERMINATED (max 120s)"
if ! wait_session_status "$SESSION_ID" 60 2 TERMINATED CANCELLED ERROR >/dev/null; then
    log_warn "session did not terminate within 120s; forcing"
    terminate_session "$SESSION_ID"
fi

# Logs may take a moment to flush; retry briefly.
log_step "Fetch logs and verify marker '${MARKER}'"
FOUND=0
for _ in {1..10}; do
    LOGS_OUT="$(./bai session logs "$SESSION_ID" 2>&1 || true)"
    if echo "$LOGS_OUT" | grep -q "$MARKER"; then FOUND=1; break; fi
    sleep 2
done

if (( FOUND == 0 )); then
    log_error "marker '${MARKER}' not found in session logs"
    echo "----- last logs output -----" >&2
    echo "$LOGS_OUT" | head -c 2000 >&2
    echo "----- end -----" >&2
    exit 1
fi

terminate_session "$SESSION_ID"

scenario_end_ok
