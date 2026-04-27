#!/usr/bin/env bash
# 05: Verify scenarios 01–04 left no orphaned user-A resources.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "05_teardown_verification"

bai_config_session
bai_login_admin
bai_login_user_a

FAIL=0

log_step "Check for leaked sessions"
LEFT_SESSIONS="$(./bai my session search --limit 200 2>&1 | PREFIX="${SCENARIO_PREFIX}-" python3 "$SCRIPT_DIR/leaked_sessions.py")"
if [[ -n "$LEFT_SESSIONS" ]]; then
    log_error "leaked sessions:"; echo "$LEFT_SESSIONS" >&2; FAIL=1
fi

log_step "Check for leaked vfolders"
LEFT_VFS="$(./bai vfolder my-search --limit 200 2>&1 | PREFIX="${SCENARIO_PREFIX}-vf-" python3 "$SCRIPT_DIR/leaked_vfolders.py")"
if [[ -n "$LEFT_VFS" ]]; then
    log_warn "vfolders still listed (may be in trash, will be purged in 99_teardown):"
    echo "$LEFT_VFS" >&2
fi

log_step "Check for leaked deployments"
LEFT_DEPS="$(./bai my deployment search --limit 200 2>&1 | PREFIX="${SCENARIO_PREFIX}-dep-" python3 "$SCRIPT_DIR/leaked_deployments.py")" || LEFT_DEPS=""
if [[ -n "$LEFT_DEPS" ]]; then
    log_error "leaked deployments:"; echo "$LEFT_DEPS" >&2; FAIL=1
fi

(( FAIL == 0 )) || { log_error "teardown verification failed"; exit 1; }

scenario_end_ok
