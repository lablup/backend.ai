#!/usr/bin/env bash
# 10: clone of a non-cloneable vfolder MUST be rejected; no destination created.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "10_vfolder_cloneable_false"

bai_config_session
bai_login_admin
bai_login_user_a

SRC_NAME="${SCENARIO_PREFIX}-vf-noclone-src-$$"
DST_NAME="${SCENARIO_PREFIX}-vf-noclone-dst-$$"

log_step "Create non-cloneable vfolder '${SRC_NAME}'"
./bai vfolder create --name "$SRC_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
SRC_ID="$(lookup_my_vfolder_id "$SRC_NAME")"
[[ -n "$SRC_ID" ]] || { log_error "src lookup failed"; exit 1; }

log_step "Clone must be rejected"
expect_fail "clone of non-cloneable vfolder" \
    ./bai vfolder clone "$SRC_ID" --name "$DST_NAME" --host "$TEST_VFOLDER_HOST"

DST_FOUND="$(lookup_my_vfolder_id "$DST_NAME" || true)"
if [[ -n "$DST_FOUND" ]]; then
    log_error "BUG: clone produced ${DST_FOUND} despite src.cloneable=false"
    ./bai vfolder delete "$DST_FOUND" >/dev/null 2>&1 || true
    ./bai vfolder purge  "$DST_FOUND" >/dev/null 2>&1 || true
    ./bai vfolder delete "$SRC_ID" >/dev/null 2>&1 || true
    ./bai vfolder purge  "$SRC_ID" >/dev/null 2>&1 || true
    exit 1
fi

log_step "Cleanup"
./bai vfolder delete "$SRC_ID" >/dev/null
./bai vfolder purge  "$SRC_ID" >/dev/null

scenario_end_ok
