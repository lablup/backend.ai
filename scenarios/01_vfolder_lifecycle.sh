#!/usr/bin/env bash
# 01: VFolder lifecycle — create → mkdir → upload → ls → mv → rm → delete → purge.
#
# Runs as user A in project A.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "01_vfolder_lifecycle"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A not found — run 00_setup.sh first"; exit 1; }
log_info "project A: $PROJECT_A_ID"

bai_login_user_a

# --- Create vfolder --------------------------------------------------------
# User-owned vfolder (no --group). Non-admin users may only create group-owned
# vfolders in MODEL_STORE projects, so user-owned is the right scope for
# regular project work.
VF_NAME="${SCENARIO_PREFIX}-vf-lifecycle-$$"
log_step "Create user-owned vfolder '${VF_NAME}' on host '${TEST_VFOLDER_HOST}'"
./bai vfolder create \
    --name "$VF_NAME" \
    --host "$TEST_VFOLDER_HOST" \
    --usage-mode general >/dev/null
log_ok "vfolder created"

# --- Confirm via my-search -------------------------------------------------
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed after create"; exit 1; }
log_ok "vfolder id: $VF_ID"
state_set vfolder_lifecycle_id "$VF_ID"

# --- mkdir -----------------------------------------------------------------
log_step "mkdir /data, /data/inputs, /data/outputs"
./bai vfolder mkdir "$VF_ID" data --parents --exist-ok >/dev/null
./bai vfolder mkdir "$VF_ID" data/inputs --exist-ok >/dev/null
./bai vfolder mkdir "$VF_ID" data/outputs --exist-ok >/dev/null
log_ok "directories created"

log_step "ls /data"
LS_OUT="$(./bai vfolder ls "$VF_ID" data 2>&1)"
echo "$LS_OUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items') or d.get('files') or []
names = [it.get('name', it.get('path', '')) for it in items] if isinstance(items, list) else []
print('listed:', names)
assert any('inputs' in (n or '') for n in names), 'inputs/ not found'
assert any('outputs' in (n or '') for n in names), 'outputs/ not found'
" || { log_error "ls verification failed: $LS_OUT"; exit 1; }
log_ok "ls /data shows inputs and outputs"

# --- mv --------------------------------------------------------------------
log_step "mv data/inputs → data/in"
./bai vfolder mv "$VF_ID" data/inputs data/in >/dev/null

# --- rm --------------------------------------------------------------------
log_step "rm data/outputs"
./bai vfolder rm "$VF_ID" data/outputs --recursive >/dev/null

# --- delete (move to trash) -----------------------------------------------
log_step "Delete vfolder (move to trash)"
./bai vfolder delete "$VF_ID" >/dev/null
log_ok "vfolder deleted (in trash)"

# --- purge -----------------------------------------------------------------
log_step "Purge vfolder"
./bai vfolder purge "$VF_ID" >/dev/null
log_ok "vfolder purged"

# --- Verify: my-search no longer shows the folder --------------------------
log_step "Verify vfolder absent from my-search"
sleep 0.5
RESIDUAL="$(lookup_my_vfolder_id "$VF_NAME" || true)"
if [[ -n "$RESIDUAL" ]]; then
    log_error "vfolder still present after purge: $RESIDUAL"
    exit 1
fi
log_ok "vfolder fully removed"

scenario_end_ok
