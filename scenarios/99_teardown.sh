#!/usr/bin/env bash
# 99: Teardown — purge all scenario test data.
# - Forcibly terminate any leaked scenario sessions
# - Delete + purge all scenario-prefixed vfolders for users A and B
# - Delete scenario users
# - Delete scenario projects

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "99_teardown"

bai_config_session
bai_login_admin

# ---- Per-user vfolder + session cleanup ----------------------------------
cleanup_user_resources() {
    local login_fn="$1" label="$2"
    log_step "${label}: terminate any scenario sessions"
    "$login_fn" || { log_warn "${label} login failed (already deleted?)"; return 0; }

    ./bai my session search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json, sys, os
prefix=os.environ['P']
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    status = (it.get('lifecycle') or {}).get('status') or it.get('status') or ''
    if name.startswith(prefix) and status not in ('TERMINATED','CANCELLED'):
        print(it['id'])
" | while read -r sid; do
        [[ -z "$sid" ]] && continue
        log_info "  terminate session $sid"
        ./bai session terminate "$sid" --forced >/dev/null 2>&1 \
            || ./bai session terminate "$sid" >/dev/null 2>&1 \
            || true
    done

    log_step "${label}: purge scenario vfolders"
    ./bai vfolder my-search --limit 500 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json,sys,os
prefix=os.environ['P']
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
DELETED={'delete-pending','delete-ongoing','delete-complete','delete-error','delete-aborted'}
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    if name.startswith(prefix) and it.get('status') not in DELETED:
        print(it['id'])
" | while read -r vid; do
        [[ -z "$vid" ]] && continue
        log_info "  delete+purge vfolder $vid"
        ./bai vfolder delete "$vid" >/dev/null 2>&1 || true
        ./bai vfolder purge  "$vid" >/dev/null 2>&1 || true
    done

    log_step "${label}: delete any scenario deployments"
    ./bai my deployment search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json,sys,os
prefix=os.environ['P']
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    if name.startswith(prefix):
        print(it['id'])
" | while read -r did; do
        [[ -z "$did" ]] && continue
        log_info "  delete deployment $did"
        ./bai deployment delete "$did" >/dev/null 2>&1 || true
    done
}

cleanup_user_resources bai_login_user_a "user A"
cleanup_user_resources bai_login_user_b "user B"

# ---- Admin: delete users + projects --------------------------------------
bai_login_admin

log_step "Delete scenario users"
for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
    USER_UID="$(lookup_user_id "$email" || true)"
    if [[ -n "$USER_UID" ]]; then
        log_info "  delete user $email ($USER_UID)"
        ./bai admin user delete "$USER_UID" >/dev/null 2>&1 || log_warn "  delete failed for $email"
    else
        log_info "  user $email not present"
    fi
done

# Clear login throttle counters in Redis so a follow-up run can log back in.
# (Soft-delete leaves these cached, and 10 failed attempts => permanent lockout.)
log_step "Clear login throttle counters in Redis"
REDIS_CONTAINER="$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis 2>/dev/null || true)"
if [[ -n "$REDIS_CONTAINER" ]]; then
    for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
        docker exec "$REDIS_CONTAINER" redis-cli del "login_history_${email}" >/dev/null 2>&1 || true
    done
    log_ok "throttle keys cleared"
else
    log_warn "halfstack redis container not found; skipping throttle clear"
fi

log_step "Delete + purge scenario projects"
for name in "$TEST_PROJECT_A_NAME" "$TEST_PROJECT_B_NAME"; do
    PID="$(lookup_project_id "$name" || true)"
    if [[ -n "$PID" ]]; then
        log_info "  delete project $name ($PID)"
        ./bai admin project delete "$PID" >/dev/null 2>&1 || log_warn "  project delete failed"
        ./bai admin project purge  "$PID" >/dev/null 2>&1 || log_warn "  project purge failed"
    fi
done

log_step "Clear local state files"
state_clear
log_ok "state cleared"

scenario_end_ok
