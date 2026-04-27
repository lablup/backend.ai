#!/usr/bin/env bash
# Setup: idempotently create scenario users (A, B), projects (A, B), memberships,
# vfolder host grants, and a model-card fixture in model-store.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "00_setup — create scenario users + projects"

bai_config_session
bai_login_admin

# Pre-clear login throttle: prior failed runs may have locked test users out.
log_step "Pre-clear login throttle counters in Redis"
REDIS_CONTAINER="$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis 2>/dev/null || true)"
if [[ -n "$REDIS_CONTAINER" ]]; then
    for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
        docker exec "$REDIS_CONTAINER" redis-cli del "login_history_${email}" >/dev/null 2>&1 || true
    done
else
    log_warn "halfstack redis container not found; skipping throttle clear"
fi

log_step "Verify domain '${TEST_DOMAIN}' exists"
./bai domain get "$TEST_DOMAIN" >/dev/null

ensure_project() {
    local name="$1"
    local existing
    existing="$(lookup_project_id "$name" || true)"
    if [[ -n "$existing" ]]; then
        printf '%s' "$existing"; return 0
    fi
    log_step "Create project '${name}'"
    local body
    body=$(printf '{"name":"%s","domain_name":"%s","resource_policy":"%s","description":"scenario test project"}' \
        "$name" "$TEST_DOMAIN" "$TEST_PROJECT_RESOURCE_POLICY")
    ./bai admin project create "$body" >/dev/null
    sleep 0.2
    local pid
    pid="$(lookup_project_id "$name")"
    [[ -n "$pid" ]] || { log_error "project create succeeded but lookup failed for '${name}'"; return 1; }
    printf '%s' "$pid"
}

PROJECT_A_ID="$(ensure_project "$TEST_PROJECT_A_NAME")"
state_set project_a_id "$PROJECT_A_ID"
PROJECT_B_ID="$(ensure_project "$TEST_PROJECT_B_NAME")"
state_set project_b_id "$PROJECT_B_ID"
log_ok "projects: A=$PROJECT_A_ID B=$PROJECT_B_ID"

ensure_user() {
    local email="$1" username="$2" password="$3"
    local existing
    existing="$(lookup_user_id "$email" || true)"
    if [[ -n "$existing" ]]; then
        # Reactivate (may be soft-deleted) + reset password + re-enable keypairs.
        local body
        body=$(printf '{"status":"active","password":"%s"}' "$password")
        ./bai user update "$existing" "$body" >/dev/null 2>&1 || true
        ./bai admin keypair search --limit 200 2>/dev/null | UID_FILTER="$existing" python3 -c "
import json, sys, os
target = os.environ['UID_FILTER']
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
for it in d.get('items', []):
    if it.get('user_id') == target and not it.get('is_active'):
        print(it['access_key'])
" | while read -r ak; do
            [[ -z "$ak" ]] && continue
            ./bai admin keypair update "{\"access_key\":\"$ak\",\"is_active\":true}" >/dev/null 2>&1 || true
        done
        printf '%s' "$existing"; return 0
    fi
    log_step "Create user '${email}'"
    ./bai admin user create \
        --email "$email" \
        --username "$username" \
        --password "$password" \
        --domain-name "$TEST_DOMAIN" \
        --status active \
        --role user \
        --resource-policy "$TEST_USER_RESOURCE_POLICY" >/dev/null
    sleep 0.3
    local uid
    uid="$(lookup_user_id "$email")"
    [[ -n "$uid" ]] || { log_error "user create succeeded but lookup failed for '${email}'"; return 1; }
    printf '%s' "$uid"
}

USER_A_ID="$(ensure_user "$TEST_USER_A_EMAIL" "$TEST_USER_A_NAME" "$TEST_USER_A_PASSWORD")"
state_set user_a_id "$USER_A_ID"
USER_B_ID="$(ensure_user "$TEST_USER_B_EMAIL" "$TEST_USER_B_NAME" "$TEST_USER_B_PASSWORD")"
state_set user_b_id "$USER_B_ID"
log_ok "users: A=$USER_A_ID B=$USER_B_ID"

# CLI for membership add isn't exposed; use the legacy GraphQL mutation.
modify_group_ok() {
    printf '%s' "$1" | python3 -c "
import json, sys
try: d = json.load(sys.stdin)
except Exception: sys.exit(1)
ok = (d.get('data', {}).get('modify_group') or d.get('modify_group') or {}).get('ok')
sys.exit(0 if ok else 1)
" 2>/dev/null
}

add_user_to_project() {
    local uid="$1" pid="$2"
    log_step "Add user $uid to project $pid"
    local query="mutation { modify_group(gid: \"${pid}\", props: {user_update_mode: \"add\", user_uuids: [\"${uid}\"]}) { ok msg } }"
    local out; out="$(./bai gql "$query" 2>&1)" || true
    modify_group_ok "$out" || log_warn "modify_group response: $out"
}

add_user_to_project "$USER_A_ID" "$PROJECT_A_ID"
add_user_to_project "$USER_B_ID" "$PROJECT_B_ID"

# Projects need allowed_vfolder_hosts populated before vfolders can be created
# bound to that host. Default is empty `{}`.
grant_host_to_project() {
    local pid="$1" host="$2"
    local perms='[\"create-vfolder\",\"modify-vfolder\",\"delete-vfolder\",\"mount-in-session\",\"upload-file\",\"download-file\",\"invite-others\",\"set-user-specific-permission\"]'
    local hosts="{\\\"${host}\\\":${perms}}"
    log_step "Grant project ${pid} access to host '${host}'"
    local query="mutation { modify_group(gid: \"${pid}\", props: {allowed_vfolder_hosts: \"${hosts}\"}) { ok msg } }"
    local out; out="$(./bai gql "$query" 2>&1)" || true
    modify_group_ok "$out" || log_warn "host grant response: $out"
}

grant_host_to_project "$PROJECT_A_ID" "$TEST_VFOLDER_HOST"
grant_host_to_project "$PROJECT_B_ID" "$TEST_VFOLDER_HOST"

log_step "Locate 'model-store' project"
MODEL_STORE_ID="$(lookup_project_id "model-store" || true)"
if [[ -z "$MODEL_STORE_ID" ]]; then
    log_warn "no 'model-store' project — scenarios 03/14 will fail until provisioned"
else
    log_ok "model-store: $MODEL_STORE_ID"
    state_set model_store_id "$MODEL_STORE_ID"
    grant_host_to_project "$MODEL_STORE_ID" "$TEST_VFOLDER_HOST"

    FIXTURE_NAME="${SCENARIO_PREFIX}-model-card-fixture"

    log_step "Ensure model fixture vfolder '${FIXTURE_NAME}' in model-store"
    FIXTURE_VFOLDER_ID="$(lookup_admin_vfolder_id "$FIXTURE_NAME" || true)"
    if [[ -z "$FIXTURE_VFOLDER_ID" ]]; then
        ./bai vfolder create \
            --name "$FIXTURE_NAME" \
            --usage-mode model \
            --group "$MODEL_STORE_ID" \
            --host "$TEST_VFOLDER_HOST" >/dev/null
        sleep 0.3
        FIXTURE_VFOLDER_ID="$(lookup_admin_vfolder_id "$FIXTURE_NAME" || true)"
        [[ -n "$FIXTURE_VFOLDER_ID" ]] || { log_error "fixture vfolder create succeeded but lookup failed"; exit 1; }
    fi
    state_set model_fixture_vfolder_id "$FIXTURE_VFOLDER_ID"

    log_step "Ensure model card '${FIXTURE_NAME}' registered"
    FIXTURE_CARD_ID="$(lookup_card_id "$FIXTURE_NAME" || true)"
    if [[ -z "$FIXTURE_CARD_ID" ]]; then
        body=$(printf '{"name":"%s","vfolder_id":"%s","model_store_project_id":"%s"}' \
            "$FIXTURE_NAME" "$FIXTURE_VFOLDER_ID" "$MODEL_STORE_ID")
        OUT="$(./bai admin model-card create "$body" 2>&1)" || log_warn "model-card create: $OUT"
        sleep 0.3
        FIXTURE_CARD_ID="$(lookup_card_id "$FIXTURE_NAME" || true)"
        [[ -n "$FIXTURE_CARD_ID" ]] || log_warn "model card not found after create — 03/14 may still fail"
    fi
    [[ -n "${FIXTURE_CARD_ID:-}" ]] && state_set model_fixture_card_id "$FIXTURE_CARD_ID"
    log_ok "fixture vfolder=$FIXTURE_VFOLDER_ID card=${FIXTURE_CARD_ID:-<missing>}"
fi

log_step "Verify each test user can log in"
bai_login_user_a
./bai my session search --limit 1 >/dev/null
bai_login_user_b
./bai my session search --limit 1 >/dev/null

# Restore admin session for downstream interactive runs.
bai_login_admin

scenario_end_ok
