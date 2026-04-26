#!/usr/bin/env bash
# Setup: Admin creates two test users (A, B) and two test projects (A, B).
# - userA is added to projectA only
# - userB is added to projectB only
# Idempotent: can be re-run safely; existing entities are reused.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "00_setup — create scenario users + projects"

bai_config_session
bai_login_admin

# Clear login throttle counters before doing anything — if a prior run failed
# mid-flight, the test users may be locked out from too many failed attempts.
log_step "Pre-clear login throttle counters in Redis"
REDIS_CONTAINER="$(docker compose -f docker-compose.halfstack.current.yml ps -q backendai-half-redis 2>/dev/null || true)"
if [[ -n "$REDIS_CONTAINER" ]]; then
    for email in "$TEST_USER_A_EMAIL" "$TEST_USER_B_EMAIL"; do
        docker exec "$REDIS_CONTAINER" redis-cli del "login_history_${email}" >/dev/null 2>&1 || true
    done
    log_ok "throttle keys cleared"
else
    log_warn "halfstack redis container not found; skipping throttle clear"
fi

# --- Resolve domain --------------------------------------------------------
log_step "Verify domain '${TEST_DOMAIN}' exists"
./bai domain get "$TEST_DOMAIN" >/dev/null
log_ok "domain '${TEST_DOMAIN}' present"

# --- Create projects -------------------------------------------------------
ensure_project() {
    local name="$1"
    local existing
    existing="$(lookup_project_id "$name" || true)"
    if [[ -n "$existing" ]]; then
        log_ok "project '${name}' already exists: $existing"
        printf '%s' "$existing"
        return 0
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
    log_ok "created project '${name}': $pid"
    printf '%s' "$pid"
}

PROJECT_A_ID="$(ensure_project "$TEST_PROJECT_A_NAME")"
state_set project_a_id "$PROJECT_A_ID"
PROJECT_B_ID="$(ensure_project "$TEST_PROJECT_B_NAME")"
state_set project_b_id "$PROJECT_B_ID"

# --- Create users ----------------------------------------------------------
ensure_user() {
    local email="$1" username="$2" password="$3"
    local existing
    existing="$(lookup_user_id "$email" || true)"
    if [[ -n "$existing" ]]; then
        # User may be soft-deleted from a prior teardown; reactivate + reset
        # password and also re-enable any keypairs (which are deactivated by
        # admin user delete) so login + API calls work in subsequent scenarios.
        log_step "Reactivate existing user '${email}' ($existing)"
        local body
        body=$(printf '{"status":"active","password":"%s"}' "$password")
        ./bai user update "$existing" "$body" >/dev/null 2>&1 \
            || log_warn "  user update failed (may be already active)"
        # Reactivate inactive keypairs for this user
        local kp_json
        kp_json="$(./bai admin keypair search --limit 200 2>/dev/null || true)"
        printf '%s' "$kp_json" | UID_FILTER="$existing" python3 -c "
import json, sys, os
target = os.environ['UID_FILTER']
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get('items', []):
    if it.get('user_id') == target and not it.get('is_active'):
        print(it['access_key'])
" | while read -r ak; do
            [[ -z "$ak" ]] && continue
            log_info "  reactivate keypair $ak"
            ./bai admin keypair update "{\"access_key\":\"$ak\",\"is_active\":true}" >/dev/null 2>&1 || true
        done
        log_ok "user '${email}' ready: $existing"
        printf '%s' "$existing"
        return 0
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
    log_ok "created user '${email}': $uid"
    printf '%s' "$uid"
}

USER_A_ID="$(ensure_user "$TEST_USER_A_EMAIL" "$TEST_USER_A_NAME" "$TEST_USER_A_PASSWORD")"
state_set user_a_id "$USER_A_ID"
USER_B_ID="$(ensure_user "$TEST_USER_B_EMAIL" "$TEST_USER_B_NAME" "$TEST_USER_B_PASSWORD")"
state_set user_b_id "$USER_B_ID"

# --- Add user → project membership ----------------------------------------
# Use GraphQL since CLI for membership add is not exposed.
add_user_to_project() {
    local uid="$1" pid="$2"
    log_step "Add user $uid to project $pid"
    # Try via GraphQL (legacy mutation that's stable across versions)
    local query
    query=$(cat <<EOF
mutation { modify_group(gid: "${pid}", props: {user_update_mode: "add", user_uuids: ["${uid}"]}) { ok msg } }
EOF
)
    local out
    out="$(./bai gql "$query" 2>&1)" || true
    if printf '%s' "$out" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
ok = (d.get('data', {}).get('modify_group') or d.get('modify_group') or {}).get('ok')
sys.exit(0 if ok else 1)
" 2>/dev/null; then
        log_ok "added (or already member)"
    else
        log_warn "modify_group response: $out"
        log_warn "membership may already exist or mutation differs in this branch"
    fi
}

add_user_to_project "$USER_A_ID" "$PROJECT_A_ID"
add_user_to_project "$USER_B_ID" "$PROJECT_B_ID"

# --- Grant projects access to the test storage host -----------------------
# Projects need allowed_vfolder_hosts populated before users (or admin) can
# create vfolders bound to that host. The default is empty `{}`.
grant_host_to_project() {
    local pid="$1" host="$2"
    local perms='[\"create-vfolder\",\"modify-vfolder\",\"delete-vfolder\",\"mount-in-session\",\"upload-file\",\"download-file\",\"invite-others\",\"set-user-specific-permission\"]'
    local hosts="{\\\"${host}\\\":${perms}}"
    log_step "Grant project ${pid} access to host '${host}'"
    local query
    query="mutation { modify_group(gid: \"${pid}\", props: {allowed_vfolder_hosts: \"${hosts}\"}) { ok msg } }"
    local out
    out="$(./bai gql "$query" 2>&1)" || true
    if printf '%s' "$out" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
ok = (d.get('data', {}).get('modify_group') or d.get('modify_group') or {}).get('ok')
sys.exit(0 if ok else 1)
" 2>/dev/null; then
        log_ok "host '${host}' granted"
    else
        log_warn "host grant response: $out"
    fi
}

grant_host_to_project "$PROJECT_A_ID" "$TEST_VFOLDER_HOST"
grant_host_to_project "$PROJECT_B_ID" "$TEST_VFOLDER_HOST"

# --- Verify: each test user can log in ------------------------------------
log_step "Verify user A login"
bai_login_user_a
./bai my session search --limit 1 >/dev/null
log_ok "user A login + self-search works"

log_step "Verify user B login"
bai_login_user_b
./bai my session search --limit 1 >/dev/null
log_ok "user B login + self-search works"

# Restore admin session for downstream scripts that may run interactively
bai_login_admin

scenario_end_ok
