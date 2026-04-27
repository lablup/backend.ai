#!/usr/bin/env bash
# 01: VFolder lifecycle — create → mkdir → ls → mv → rm → delete → purge.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "01_vfolder_lifecycle"

bai_config_session
bai_login_admin
PROJECT_A_ID="$(state_get project_a_id || lookup_project_id "$TEST_PROJECT_A_NAME")"
[[ -n "$PROJECT_A_ID" ]] || { log_error "project A not found — run 00_setup.sh first"; exit 1; }

bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-lifecycle-$$"
log_step "Create user-owned vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" --usage-mode general >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed after create"; exit 1; }
state_set vfolder_lifecycle_id "$VF_ID"
log_ok "vfolder: $VF_ID"

log_step "mkdir data/inputs, data/outputs"
./bai vfolder mkdir "$VF_ID" data --parents --exist-ok >/dev/null
./bai vfolder mkdir "$VF_ID" data/inputs --exist-ok >/dev/null
./bai vfolder mkdir "$VF_ID" data/outputs --exist-ok >/dev/null

log_step "ls /data must show inputs and outputs"
./bai vfolder ls "$VF_ID" data 2>&1 | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items') or d.get('files') or []
names = [it.get('name', it.get('path', '')) for it in items] if isinstance(items, list) else []
assert any('inputs' in (n or '') for n in names), f'inputs/ not found in {names}'
assert any('outputs' in (n or '') for n in names), f'outputs/ not found in {names}'
" || { log_error "ls verification failed"; exit 1; }

log_step "mv data/inputs → data/in"
./bai vfolder mv "$VF_ID" data/inputs data/in >/dev/null

log_step "rm data/outputs"
./bai vfolder rm "$VF_ID" data/outputs --recursive >/dev/null

log_step "delete + purge"
./bai vfolder delete "$VF_ID" >/dev/null
./bai vfolder purge "$VF_ID" >/dev/null

log_step "Verify vfolder absent from my-search"
sleep 0.5
RESIDUAL="$(lookup_my_vfolder_id "$VF_NAME" || true)"
[[ -z "$RESIDUAL" ]] || { log_error "vfolder still present after purge: $RESIDUAL"; exit 1; }

scenario_end_ok
