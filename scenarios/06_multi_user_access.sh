#!/usr/bin/env bash
# 06: User B cannot see user A's vfolder via my-search or by id.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "06_multi_user_access"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-multiuser-$$"
log_step "user A: create vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "lookup failed"; exit 1; }
log_ok "vfolder: $VF_ID"

bai_login_user_b

log_step "user B: my-search must NOT contain user A's vfolder"
./bai vfolder my-search --limit 200 2>&1 | VID="$VF_ID" python3 -c "
import json, sys, os
target = os.environ['VID']
for it in json.load(sys.stdin).get('items', []):
    if it.get('id') == target: sys.exit(1)
sys.exit(0)
" || { log_error "isolation broken: user B can see user A's vfolder"; exit 1; }

log_step "user B: direct vfolder get by id should fail"
expect_fail "user B accessing user A's vfolder by id" \
    ./bai vfolder get "$VF_ID"

bai_login_user_a
log_step "user A: cleanup"
./bai vfolder delete "$VF_ID" >/dev/null || true
./bai vfolder purge "$VF_ID" >/dev/null || true

scenario_end_ok
