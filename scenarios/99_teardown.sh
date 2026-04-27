#!/usr/bin/env bash
# 99: Teardown — purge every scenario-prefixed resource and the test users.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "99_teardown"

bai_config_session
bai_login_admin

cleanup_user_resources() {
    local login_fn="$1" label="$2"
    "$login_fn" || { log_warn "${label} login failed (already deleted?)"; return 0; }

    log_step "${label}: terminate scenario sessions"
    ./bai my session search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json, sys, os
prefix = os.environ['P']
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    status = (it.get('lifecycle') or {}).get('status') or it.get('status') or ''
    if name.startswith(prefix) and status not in ('TERMINATED','CANCELLED'):
        print(it['id'])
" | while read -r sid; do
        [[ -z "$sid" ]] && continue
        terminate_session "$sid"
    done

    log_step "${label}: purge scenario vfolders"
    ./bai vfolder my-search --limit 500 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json, sys, os
prefix = os.environ['P']
DELETED = {'delete-pending','delete-ongoing','delete-complete','delete-error','delete-aborted'}
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    if name.startswith(prefix) and it.get('status') not in DELETED:
        print(it['id'])
" | while read -r vid; do
        [[ -z "$vid" ]] && continue
        ./bai vfolder delete "$vid" >/dev/null 2>&1 || true
        ./bai vfolder purge  "$vid" >/dev/null 2>&1 || true
    done

    log_step "${label}: delete scenario deployments"
    ./bai my deployment search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json, sys, os
prefix = os.environ['P']
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    if name.startswith(prefix): print(it['id'])
" | while read -r did; do
        [[ -z "$did" ]] && continue
        ./bai deployment delete "$did" >/dev/null 2>&1 || true
    done
}

cleanup_user_resources bai_login_user_a "user A"
cleanup_user_resources bai_login_user_b "user B"

bai_login_admin

# Model card fixture — created by 00_setup in `model-store`. Delete the card
# first (frees the vfolder reference), then the vfolder.
FIXTURE_NAME="${SCENARIO_PREFIX}-model-card-fixture"

log_step "Delete model card fixture"
FIXTURE_CARD_ID="$(state_get model_fixture_card_id || lookup_card_id "$FIXTURE_NAME" || true)"
if [[ -n "$FIXTURE_CARD_ID" ]]; then
    ./bai admin model-card delete "$FIXTURE_CARD_ID" >/dev/null 2>&1 || log_warn "model card delete failed"
fi

log_step "Delete model fixture vfolder"
FIXTURE_VF_ID="$(state_get model_fixture_vfolder_id || lookup_admin_vfolder_id "$FIXTURE_NAME" || true)"
if [[ -n "$FIXTURE_VF_ID" ]]; then
    ./bai vfolder delete "$FIXTURE_VF_ID" >/dev/null 2>&1 || true
    ./bai vfolder purge  "$FIXTURE_VF_ID" >/dev/null 2>&1 || true
fi

log_step "Delete scenario users"
for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
    USER_UID="$(lookup_user_id "$email" || true)"
    if [[ -n "$USER_UID" ]]; then
        ./bai admin user delete "$USER_UID" >/dev/null 2>&1 || log_warn "delete failed for $email"
    fi
done

# Soft-delete leaves login_history_<email> Redis keys cached. 10 failed
# attempts → permanent lockout, so clear before next run.
log_step "Clear login throttle counters in Redis"
REDIS_CONTAINER="$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis 2>/dev/null || true)"
if [[ -n "$REDIS_CONTAINER" ]]; then
    for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
        docker exec "$REDIS_CONTAINER" redis-cli del "login_history_${email}" >/dev/null 2>&1 || true
    done
else
    log_warn "halfstack redis container not found; skipping throttle clear"
fi

log_step "Delete + purge scenario projects"
for name in "$TEST_PROJECT_A_NAME" "$TEST_PROJECT_B_NAME"; do
    PID="$(lookup_project_id "$name" || true)"
    if [[ -n "$PID" ]]; then
        ./bai admin project delete "$PID" >/dev/null 2>&1 || log_warn "project delete failed"
        ./bai admin project purge  "$PID" >/dev/null 2>&1 || log_warn "project purge failed"
    fi
done

log_step "Clear local state files"
state_clear

scenario_end_ok
