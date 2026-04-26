#!/usr/bin/env bash
# 13: BATCH session prints expected output and `session logs` retrieves it.
# - Enqueue BATCH session with startup_command="echo <marker>"
# - Wait for TERMINATED (batch self-exits when command finishes)
# - `session logs` MUST contain the marker

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "13_session_exec_logs"

bai_config_session
bai_login_admin

PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A missing"; exit 1; }

log_step "Resolve image id for '${TEST_IMAGE_NAME}'"
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
SESSION_ID="$(echo "$ENQ_OUT" | python3 -c "
import json, sys
try: d = json.load(sys.stdin)
except Exception: sys.exit(1)
sid = (d.get('session') or {}).get('id') or d.get('id') or d.get('session_id')
if sid: print(sid)
")"
[[ -n "$SESSION_ID" ]] || { log_error "enqueue failed"; echo "$ENQ_OUT" >&2; exit 1; }
log_ok "session: $SESSION_ID"

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

# Wait for the BATCH session to finish (TERMINATED) — startup_command runs once
# and the session self-exits.
log_step "Wait for BATCH session to TERMINATED (max 120s)"
TERMINATED=0
for _ in {1..60}; do
    s="$(_session_status)"
    log_debug "status: $s"
    case "$s" in
        TERMINATED|CANCELLED|ERROR) TERMINATED=1; break ;;
    esac
    sleep 2
done

if (( TERMINATED == 0 )); then
    log_warn "session did not terminate within 120s; forcing"
    ./bai session terminate "$SESSION_ID" --forced >/dev/null 2>&1 || true
fi

# Logs may take a moment to be flushed/collected; retry briefly.
log_step "Fetch container logs and verify marker '${MARKER}'"
FOUND=0
for _ in {1..10}; do
    LOGS_OUT="$(./bai session logs "$SESSION_ID" 2>&1 || true)"
    if echo "$LOGS_OUT" | grep -q "$MARKER"; then
        FOUND=1; break
    fi
    sleep 2
done

if (( FOUND == 0 )); then
    log_error "marker '${MARKER}' not found in session logs"
    echo "----- last logs output -----"
    echo "$LOGS_OUT" | head -c 2000
    echo "----- end -----"
    exit 1
fi
log_ok "marker present in container logs"

log_step "Cleanup (terminate if still alive)"
./bai session terminate "$SESSION_ID" --forced >/dev/null 2>&1 || true

scenario_end_ok
