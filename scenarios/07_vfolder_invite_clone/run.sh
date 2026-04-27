#!/usr/bin/env bash
# 07: vfolder clone — cloneable=true → both src and dst readable, both contain populated dir.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "07_vfolder_invite_clone"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

bai_login_user_a

SRC_NAME="${SCENARIO_PREFIX}-vf-cloneable-src-$$"
DST_NAME="${SCENARIO_PREFIX}-vf-cloneable-dst-$$"

log_step "Create cloneable vfolder '${SRC_NAME}' + populate /shared"
./bai vfolder create --name "$SRC_NAME" --host "$TEST_VFOLDER_HOST" --cloneable >/dev/null
SRC_ID="$(lookup_my_vfolder_id "$SRC_NAME")"
[[ -n "$SRC_ID" ]] || { log_error "src lookup failed"; exit 1; }
./bai vfolder mkdir "$SRC_ID" shared --exist-ok >/dev/null

log_step "Clone src → '${DST_NAME}'"
./bai vfolder clone "$SRC_ID" --name "$DST_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
DST_ID="$(lookup_my_vfolder_id "$DST_NAME")"
[[ -n "$DST_ID" ]] || { log_error "cloned vfolder lookup failed"; exit 1; }

log_step "Both src and dst must contain /shared"
./bai vfolder ls "$SRC_ID" / 2>&1 | grep -q "shared" \
    || { log_error "src missing /shared after clone"; exit 1; }
./bai vfolder ls "$DST_ID" / 2>&1 | grep -q "shared" \
    || { log_error "dst missing /shared after clone"; exit 1; }

log_step "Cleanup"
./bai vfolder delete "$SRC_ID" >/dev/null
./bai vfolder purge  "$SRC_ID" >/dev/null
./bai vfolder delete "$DST_ID" >/dev/null
./bai vfolder purge  "$DST_ID" >/dev/null

scenario_end_ok
