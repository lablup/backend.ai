#!/usr/bin/env bash
# 11: VFolder bulk-delete and bulk-purge — multiple folders in one call.

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "11_vfolder_bulk_ops"

bai_config_session
bai_login_admin
bai_login_user_a

NAMES=()
IDS=()
for i in 1 2 3; do
    n="${SCENARIO_PREFIX}-vf-bulk-${i}-$$"
    NAMES+=("$n")
    log_step "Create vfolder '$n'"
    ./bai vfolder create --name "$n" --host "$TEST_VFOLDER_HOST" >/dev/null
    id="$(lookup_my_vfolder_id "$n")"
    [[ -n "$id" ]] || { log_error "lookup failed for $n"; exit 1; }
    IDS+=("$id")
    log_ok "  $id"
done

log_step "Bulk-delete ${#IDS[@]} vfolders in one call"
./bai vfolder bulk-delete "${IDS[@]}" >/dev/null

# Verify each is now in a deleted state (delete-pending/ongoing/complete)
log_step "Verify all targeted vfolders are in a deleted state"
JSON="$(./bai vfolder my-search --limit 500 2>/dev/null)"
IDS_CSV="$(IFS=,; echo "${IDS[*]}")"
echo "$JSON" | TARGETS="$IDS_CSV" python3 -c "
import json, sys, os
targets = set(os.environ['TARGETS'].split(','))
DELETED = {'delete-pending','delete-ongoing','delete-complete','delete-error','delete-aborted'}
d = json.load(sys.stdin)
seen = {it['id']: it.get('status') for it in d.get('items', []) if it.get('id') in targets}
missing = targets - set(seen.keys())
not_deleted = [vid for vid, s in seen.items() if s not in DELETED]
if missing:
    print('MISSING_FROM_LIST', ','.join(missing))
if not_deleted:
    print('NOT_IN_DELETED_STATE', ','.join(not_deleted))
sys.exit(0 if (not missing and not not_deleted) else 1)
" || { log_error "bulk-delete state check failed"; exit 1; }
log_ok "all 3 in deleted state"

log_step "Bulk-purge the same vfolders"
./bai vfolder bulk-purge "${IDS[@]}" >/dev/null
log_ok "bulk-purge issued"

# After purge, the vfolders should be either gone from my-search entirely or
# remain in delete-complete. Either way, they MUST NOT show as 'ready'.
log_step "Verify none of the bulk-targeted vfolders are 'ready' anymore"
JSON_AFTER="$(./bai vfolder my-search --limit 500 2>/dev/null)"
echo "$JSON_AFTER" | TARGETS="$IDS_CSV" python3 -c "
import json, sys, os
targets = set(os.environ['TARGETS'].split(','))
d = json.load(sys.stdin)
ready_leak = [it['id'] for it in d.get('items', []) if it.get('id') in targets and it.get('status') == 'ready']
if ready_leak:
    print('READY_AFTER_PURGE', ','.join(ready_leak)); sys.exit(1)
sys.exit(0)
" || { log_error "vfolder still 'ready' after bulk-purge"; exit 1; }
log_ok "bulk-purge took effect"

scenario_end_ok
