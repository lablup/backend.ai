#!/usr/bin/env bash
# Shared helpers for scenario scripts. Most JSON parsing lives in $SCN_PY/*.py.

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

# ---- bai login helpers ----
_bai_login_as() {
    local email="$1" password="$2" label="$3"
    ./bai logout >/dev/null 2>&1 || true
    local out
    out="$(BACKEND_USER="$email" BACKEND_PASSWORD="$password" ./bai login 2>&1)" || {
        if ! printf '%s' "$out" | grep -qi "already logged in"; then
            log_error "${label} login failed: $out"
            return 1
        fi
    }
    return 0
}

bai_login_admin()  { _bai_login_as "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "admin"; }
bai_login_user_a() { _bai_login_as "$TEST_USER_A_EMAIL" "$TEST_USER_A_PASSWORD" "user A"; }
bai_login_user_b() { _bai_login_as "$TEST_USER_B_EMAIL" "$TEST_USER_B_PASSWORD" "user B"; }

bai_config_session() {
    ./bai config set endpoint "$BAI_ENDPOINT" >/dev/null
    ./bai config set endpoint-type "$BAI_ENDPOINT_TYPE" >/dev/null
}

# wait_until <timeout-seconds> <interval-seconds> <test-command...>
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

lookup_project_id() {
    ./bai admin project search --limit 50 2>&1 | NAME="$1" python3 "$SCN_PY/lookup_project_id.py"
}

lookup_user_id() {
    ./bai admin user search --email-contains "$1" --limit 5 2>&1 | EMAIL="$1" python3 "$SCN_PY/lookup_user_id.py"
}

lookup_image_id() {
    ./bai admin image search --name-contains "$1" --limit 50 2>&1 | NAME="$1" python3 "$SCN_PY/lookup_image_id.py"
}

# Skips deleted states. Used from a user context (user-owned vfolders).
lookup_my_vfolder_id() {
    ./bai vfolder my-search --limit 200 2>&1 | NAME="$1" python3 "$SCN_PY/lookup_vfolder_id.py"
}

# Admin context: any vfolder by exact name, skipping deleted.
lookup_admin_vfolder_id() {
    ./bai vfolder admin-search --limit 500 2>&1 | NAME="$1" python3 "$SCN_PY/lookup_vfolder_id.py"
}

# Project-scoped vfolder lookup (caller chooses whether admin or member).
lookup_project_vfolder_id() {
    ./bai vfolder project-search "$1" --limit 200 2>/dev/null | NAME="$2" python3 "$SCN_PY/lookup_vfolder_id.py"
}

lookup_card_id() {
    ./bai admin model-card search --name-contains "$1" --limit 10 2>&1 | NAME="$1" python3 "$SCN_PY/lookup_card_id.py"
}

# ---- Response parsers (read JSON from stdin) ----

session_id_from()    { python3 "$SCN_PY/session_id_from.py"; }
deployment_id_from() { python3 "$SCN_PY/deployment_id_from.py"; }

# ---- Session state machine ----

# Print live status of a session id (querying current user's my-search).
session_status() {
    SID="$1" ./bai my session search --limit 50 2>/dev/null | SID="$1" python3 "$SCN_PY/session_status.py"
}

# wait_session_status <sid> <iters> <interval> <state> [<state>...]
# Returns 0 on first match (echoing the matched status). On timeout returns 1
# and echoes the last observed status.
wait_session_status() {
    local sid="$1" iters="$2" interval="$3"; shift 3
    local s=""
    for ((i=0; i<iters; i++)); do
        s="$(session_status "$sid")"
        log_debug "session ${sid:0:8} status: $s"
        for want in "$@"; do
            if [[ "$s" == "$want" ]]; then printf '%s' "$s"; return 0; fi
        done
        sleep "$interval"
    done
    printf '%s' "$s"
    return 1
}

# Best-effort terminate; never errors out.
terminate_session() {
    local sid="$1"
    ./bai session terminate "$sid" --forced >/dev/null 2>&1 \
        || ./bai session terminate "$sid" >/dev/null 2>&1 \
        || true
}

# Build an interactive session enqueue payload (1 CPU, 1 GiB RAM).
# Usage: session_payload <name> <image_id> <project_id> [vfolder_id mount_path]
session_payload() {
    local name="$1" image_id="$2" pid="$3"
    local mounts="[]"
    if [[ -n "${4:-}" && -n "${5:-}" ]]; then
        mounts=$(printf '[{"vfolder_id":"%s","mount_path":"%s","permission":"rw"}]' "$4" "$5")
    fi
    cat <<EOF
{
  "session_name": "${name}",
  "session_type": "interactive",
  "image_id": "${image_id}",
  "resource_entries": [
    {"resource_type": "cpu", "quantity": "1"},
    {"resource_type": "mem", "quantity": "1073741824"}
  ],
  "resource_group": "${TEST_RESOURCE_GROUP}",
  "project_id": "${pid}",
  "mounts": ${mounts}
}
EOF
}

# ---- State persistence ----

state_set() { printf '%s' "$2" > "$SCENARIO_STATE_DIR/$1"; }
state_get() { [[ -f "$SCENARIO_STATE_DIR/$1" ]] && cat "$SCENARIO_STATE_DIR/$1" || return 1; }
state_clear() { rm -rf "$SCENARIO_STATE_DIR"/*; }

# ---- Negative-path assertion ----
expect_fail() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        log_error "expected '${desc}' to fail but it succeeded"
        return 1
    fi
    log_ok "expected failure: ${desc}"
}
