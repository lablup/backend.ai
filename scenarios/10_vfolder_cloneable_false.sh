#!/usr/bin/env bash
# 10: VFolder clone negative — non-cloneable folder MUST reject clone.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "10_vfolder_cloneable_false"

bai_config_session
bai_login_admin
bai_login_user_a

SRC_NAME="${SCENARIO_PREFIX}-vf-noclone-src-$$"
DST_NAME="${SCENARIO_PREFIX}-vf-noclone-dst-$$"

log_step "Create non-cloneable user-owned vfolder '${SRC_NAME}'"
./bai vfolder create --name "$SRC_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
SRC_ID="$(lookup_my_vfolder_id "$SRC_NAME")"
[[ -n "$SRC_ID" ]] || { log_error "src lookup failed"; exit 1; }
log_ok "src: $SRC_ID (cloneable=false by default)"

log_step "Attempt clone — must be rejected"
expect_fail "clone of non-cloneable vfolder" \
    ./bai vfolder clone "$SRC_ID" --name "$DST_NAME" --host "$TEST_VFOLDER_HOST"

# Make sure no destination vfolder slipped through
DST_FOUND="$(lookup_my_vfolder_id "$DST_NAME" || true)"
if [[ -n "$DST_FOUND" ]]; then
    log_error "BUG: clone produced ${DST_FOUND} despite src.cloneable=false"
    ./bai vfolder delete "$DST_FOUND" >/dev/null 2>&1 || true
    ./bai vfolder purge  "$DST_FOUND" >/dev/null 2>&1 || true
    ./bai vfolder delete "$SRC_ID" >/dev/null 2>&1 || true
    ./bai vfolder purge  "$SRC_ID" >/dev/null 2>&1 || true
    exit 1
fi
log_ok "no destination vfolder created"

log_step "Cleanup"
./bai vfolder delete "$SRC_ID" >/dev/null
./bai vfolder purge  "$SRC_ID" >/dev/null

scenario_end_ok
