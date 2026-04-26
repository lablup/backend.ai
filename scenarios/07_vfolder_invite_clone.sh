#!/usr/bin/env bash
# 07: VFolder clone.
# - User A creates a cloneable vfolder + populates it with a directory
# - User A clones it to a new vfolder name
# - Verify clone exists, original still exists, both contain the directory
# - Cleanup
#
# Note: vfolder invite (sharing across users) is not exposed in the v2 CLI.
# Clone is the lifecycle operation that's available; we exercise it here.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "07_vfolder_invite_clone"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

bai_login_user_a

SRC_NAME="${SCENARIO_PREFIX}-vf-cloneable-src-$$"
DST_NAME="${SCENARIO_PREFIX}-vf-cloneable-dst-$$"

log_step "Create cloneable user-owned vfolder '${SRC_NAME}'"
./bai vfolder create \
    --name "$SRC_NAME" \
    --host "$TEST_VFOLDER_HOST" \
    --cloneable >/dev/null
SRC_ID="$(lookup_my_vfolder_id "$SRC_NAME")"
[[ -n "$SRC_ID" ]] || { log_error "src lookup failed"; exit 1; }
log_ok "src: $SRC_ID"

log_step "Populate src with /shared dir"
./bai vfolder mkdir "$SRC_ID" shared --exist-ok >/dev/null

log_step "Clone src → '${DST_NAME}'"
./bai vfolder clone "$SRC_ID" --name "$DST_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null

DST_ID="$(lookup_my_vfolder_id "$DST_NAME")"
[[ -n "$DST_ID" ]] || { log_error "cloned vfolder lookup failed"; exit 1; }
log_ok "clone: $DST_ID"

log_step "Verify src still contains /shared"
./bai vfolder ls "$SRC_ID" / 2>&1 | grep -q "shared" \
    || { log_error "src missing /shared after clone"; exit 1; }
log_ok "src /shared present"

log_step "Verify dst contains /shared (clone copied data)"
./bai vfolder ls "$DST_ID" / 2>&1 | grep -q "shared" \
    || { log_error "dst missing /shared after clone"; exit 1; }
log_ok "dst /shared present"

log_step "Cleanup"
./bai vfolder delete "$SRC_ID" >/dev/null
./bai vfolder purge  "$SRC_ID" >/dev/null
./bai vfolder delete "$DST_ID" >/dev/null
./bai vfolder purge  "$DST_ID" >/dev/null

scenario_end_ok
