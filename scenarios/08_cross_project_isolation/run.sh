#!/usr/bin/env bash
# 08: Cross-project isolation — project-search never crosses project boundaries.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "08_cross_project_isolation"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
PROJECT_B_ID="$(state_get project_b_id || lookup_project_id "$TEST_PROJECT_B_NAME")"
[[ -n "$PROJECT_A_ID" && -n "$PROJECT_B_ID" ]] || { log_error "missing projects"; exit 1; }

VFA_NAME="${SCENARIO_PREFIX}-vf-isoA-$$"
VFB_NAME="${SCENARIO_PREFIX}-vf-isoB-$$"

log_step "admin: create project-A vfolder + project-B vfolder"
./bai vfolder create --name "$VFA_NAME" --host "$TEST_VFOLDER_HOST" --group "$PROJECT_A_ID" >/dev/null
VFA_ID="$(lookup_project_vfolder_id "$PROJECT_A_ID" "$VFA_NAME")"
[[ -n "$VFA_ID" ]] || { log_error "VFA lookup failed"; exit 1; }
./bai vfolder create --name "$VFB_NAME" --host "$TEST_VFOLDER_HOST" --group "$PROJECT_B_ID" >/dev/null
VFB_ID="$(lookup_project_vfolder_id "$PROJECT_B_ID" "$VFB_NAME")"
[[ -n "$VFB_ID" ]] || { log_error "VFB lookup failed"; exit 1; }
log_ok "VFA: $VFA_ID, VFB: $VFB_ID"

log_step "project-search(A) lists VFA but NOT VFB"
EXPECT="$VFA_ID" FORBID="$VFB_ID" ./bai vfolder project-search "$PROJECT_A_ID" --limit 200 2>&1 \
    | EXPECT="$VFA_ID" FORBID="$VFB_ID" python3 "$SCRIPT_DIR/assert_listing.py" \
    || { log_error "project-search(A) isolation failed"; exit 1; }

log_step "project-search(B) lists VFB but NOT VFA"
EXPECT="$VFB_ID" FORBID="$VFA_ID" ./bai vfolder project-search "$PROJECT_B_ID" --limit 200 2>&1 \
    | EXPECT="$VFB_ID" FORBID="$VFA_ID" python3 "$SCRIPT_DIR/assert_listing.py" \
    || { log_error "project-search(B) isolation failed"; exit 1; }

bai_login_user_a

log_step "user A: project-search(B) must NOT reveal VFB"
A_PB_OUT="$(./bai vfolder project-search "$PROJECT_B_ID" --limit 200 2>&1 || true)"
echo "$A_PB_OUT" | TARGET="$VFB_ID" python3 "$SCN_PY/check_no_id.py" \
    || { log_error "user A leaked VFB via project-search(B)"; exit 1; }

bai_login_admin
log_step "Cleanup"
./bai vfolder delete "$VFA_ID" >/dev/null || true
./bai vfolder purge  "$VFA_ID" >/dev/null || true
./bai vfolder delete "$VFB_ID" >/dev/null || true
./bai vfolder purge  "$VFB_ID" >/dev/null || true

scenario_end_ok
