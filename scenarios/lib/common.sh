#!/usr/bin/env bash
# Shared helpers for scenario scripts.

# ---- Colors / logging ----
if [[ -t 1 ]]; then
    _C_RED=$'\033[0;31m'
    _C_GREEN=$'\033[0;32m'
    _C_YELLOW=$'\033[0;33m'
    _C_BLUE=$'\033[0;34m'
    _C_GRAY=$'\033[0;37m'
    _C_BOLD=$'\033[1m'
    _C_RESET=$'\033[0m'
else
    _C_RED= _C_GREEN= _C_YELLOW= _C_BLUE= _C_GRAY= _C_BOLD= _C_RESET=
fi

log_info()    { printf '%s[INFO]%s %s\n' "$_C_BLUE" "$_C_RESET" "$*" >&2; }
log_step()    { printf '%s%s[STEP]%s %s\n' "$_C_BOLD" "$_C_BLUE" "$_C_RESET" "$*" >&2; }
log_ok()      { printf '%s[ OK ]%s %s\n' "$_C_GREEN" "$_C_RESET" "$*" >&2; }
log_warn()    { printf '%s[WARN]%s %s\n' "$_C_YELLOW" "$_C_RESET" "$*" >&2; }
log_error()   { printf '%s[FAIL]%s %s\n' "$_C_RED" "$_C_RESET" "$*" >&2; }
log_debug()   { [[ -n "${SCENARIO_DEBUG:-}" ]] && printf '%s[DBUG]%s %s\n' "$_C_GRAY" "$_C_RESET" "$*" >&2 || true; }

# ---- Scenario header / footer ----
_SCENARIO_NAME=""
_SCENARIO_START=0

scenario_begin() {
    _SCENARIO_NAME="$1"
    _SCENARIO_START=$(date +%s)
    printf '\n%s========================================================================%s\n' "$_C_BOLD" "$_C_RESET" >&2
    printf '%s SCENARIO: %s%s\n' "$_C_BOLD" "$_SCENARIO_NAME" "$_C_RESET" >&2
    printf '%s========================================================================%s\n' "$_C_BOLD" "$_C_RESET" >&2
}

scenario_end_ok() {
    local end=$(date +%s)
    local dur=$((end - _SCENARIO_START))
    log_ok "Scenario '${_SCENARIO_NAME}' PASSED (${dur}s)"
}

# ---- JSON helpers (prefers jq; falls back to python3) ----
HAVE_JQ=0
if command -v jq >/dev/null 2>&1; then HAVE_JQ=1; fi

# json_get <json> <path>
#   Path is jq-style: .items[0].id  OR python-style with same dotted form (also supports [n])
json_get() {
    local data="$1" path="$2"
    if [[ "$HAVE_JQ" == "1" ]]; then
        printf '%s' "$data" | jq -r "$path"
    else
        printf '%s' "$data" | python3 -c "
import json, sys, re
d = json.load(sys.stdin)
expr = sys.argv[1].lstrip('.')
def walk(obj, expr):
    while expr:
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)', expr)
        if m:
            key = m.group(1); expr = expr[len(key):]
            if obj is None: return None
            obj = obj.get(key)
        elif expr.startswith('['):
            m = re.match(r'^\[(-?\d+)\]', expr)
            if not m: raise SystemExit('bad expr')
            idx = int(m.group(1)); expr = expr[m.end():]
            if obj is None: return None
            try: obj = obj[idx]
            except (IndexError, KeyError, TypeError): return None
        elif expr.startswith('.'):
            expr = expr[1:]
        else:
            raise SystemExit(f'bad expr at: {expr}')
    return obj
v = walk(d, expr)
if v is None: print('null')
elif isinstance(v, (dict, list)): print(json.dumps(v))
else: print(v)
" "$path"
    fi
}

# ---- bai login helpers ----

# Login as <email> <password>; logs out first to switch users cleanly.
_bai_login_as() {
    local email="$1" password="$2" label="$3"
    log_debug "Login as ${email}"
    ./bai logout >/dev/null 2>&1 || true
    local out
    out="$(BACKEND_USER="$email" BACKEND_PASSWORD="$password" ./bai login 2>&1)" || {
        # Tolerate "already logged in" — verify identity below
        if ! printf '%s' "$out" | grep -qi "already logged in"; then
            log_error "${label} login failed: $out"
            return 1
        fi
    }
    # Confirm we're actually logged in as the requested user
    local current
    current="$(./bai config show 2>&1 | grep -Ei '^[[:space:]]*(email|user)' | head -1 || true)"
    log_debug "config-show: $current"
    return 0
}

bai_login_admin()  { _bai_login_as "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "admin"; }
bai_login_user_a() { _bai_login_as "$TEST_USER_A_EMAIL" "$TEST_USER_A_PASSWORD" "user A"; }
bai_login_user_b() { _bai_login_as "$TEST_USER_B_EMAIL" "$TEST_USER_B_PASSWORD" "user B"; }

# Configure session endpoint (called once, idempotent)
bai_config_session() {
    ./bai config set endpoint "$BAI_ENDPOINT" >/dev/null
    ./bai config set endpoint-type "$BAI_ENDPOINT_TYPE" >/dev/null
}

# ---- Wait helpers ----

# wait_until <timeout-seconds> <interval-seconds> <test-command...>
# returns 0 once command exits 0; returns 1 if timed out.
wait_until() {
    local timeout="$1" interval="$2"; shift 2
    local elapsed=0
    while (( elapsed < timeout )); do
        if "$@" >/dev/null 2>&1; then return 0; fi
        sleep "$interval"
        elapsed=$(( elapsed + interval ))
    done
    return 1
}

# ---- ID lookup helpers ----

# Lookup project UUID by name (admin context required)
lookup_project_id() {
    local name="$1"
    local out
    out="$(./bai admin project search --limit 50 2>&1)" || { log_error "project search failed: $out"; return 1; }
    printf '%s' "$out" | python3 -c "
import json, sys
target = sys.argv[1]
data = json.load(sys.stdin)
for it in data.get('items', []):
    if it.get('basic_info', {}).get('name') == target:
        print(it['id']); break
" "$name"
}

# Lookup user UUID by email (admin context required)
lookup_user_id() {
    local email="$1"
    local out
    out="$(./bai admin user search --email-contains "$email" --limit 5 2>&1)" || { log_error "user search failed: $out"; return 1; }
    printf '%s' "$out" | python3 -c "
import json, sys
data = json.load(sys.stdin)
target = sys.argv[1]
for it in data.get('items', []):
    info = it.get('basic_info') or {}
    if info.get('email') == target or it.get('email') == target:
        print(it['id']); break
" "$email"
}

# Lookup image UUID by name (admin context required)
lookup_image_id() {
    local name="$1"
    local out
    out="$(./bai admin image search --name-contains "$name" --limit 50 2>&1)" || { log_error "image search failed"; return 1; }
    printf '%s' "$out" | python3 -c "
import json, sys
data = json.load(sys.stdin)
target = sys.argv[1]
for it in data.get('items', []):
    if it.get('name') == target:
        print(it['id']); break
" "$name"
}

# Lookup vfolder ID by name within current user context.
# Skips vfolders in any deleted state (delete-pending, delete-ongoing,
# delete-complete, delete-error).
lookup_my_vfolder_id() {
    local name="$1"
    local out
    out="$(./bai vfolder my-search --limit 200 2>&1)" || return 1
    printf '%s' "$out" | python3 -c "
import json, sys
data = json.load(sys.stdin)
target = sys.argv[1]
DELETED = {'delete-pending', 'delete-ongoing', 'delete-complete', 'delete-error', 'delete-aborted'}
for it in data.get('items', []):
    md = it.get('metadata') or {}
    name_v = md.get('name') or it.get('name')
    if name_v != target: continue
    if it.get('status') in DELETED: continue
    print(it['id']); break
" "$name"
}

# State persistence
state_set() {
    local key="$1" val="$2"
    printf '%s' "$val" > "$SCENARIO_STATE_DIR/$key"
}

state_get() {
    local key="$1"
    [[ -f "$SCENARIO_STATE_DIR/$key" ]] && cat "$SCENARIO_STATE_DIR/$key" || return 1
}

state_clear() {
    rm -rf "$SCENARIO_STATE_DIR"/*
}

# Run a step that's expected to FAIL with a 4xx-like error.
# Use this to verify access-control denials.
expect_fail() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        log_error "expected '${desc}' to fail but it succeeded"
        return 1
    else
        log_ok "expected failure: ${desc}"
        return 0
    fi
}

# Pretty wrapper around bai that pipes JSON nicely on stderr when SCENARIO_DEBUG is set
bai() {
    if [[ -n "${SCENARIO_DEBUG:-}" ]]; then
        log_debug "./bai $*"
    fi
    ./bai "$@"
}
