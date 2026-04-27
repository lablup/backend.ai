#!/usr/bin/env bash
# 11: bulk-delete + bulk-purge across multiple vfolders in one call.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "11_vfolder_bulk_ops"

bai_config_session
bai_login_admin
bai_login_user_a

IDS=()
for i in 1 2 3; do
    n="${SCENARIO_PREFIX}-vf-bulk-${i}-$$"
    log_step "Create vfolder '$n'"
    ./bai vfolder create --name "$n" --host "$TEST_VFOLDER_HOST" >/dev/null
    id="$(lookup_my_vfolder_id "$n")"
    [[ -n "$id" ]] || { log_error "lookup failed for $n"; exit 1; }
    IDS+=("$id")
done

log_step "Bulk-delete ${#IDS[@]} vfolders in one call"
./bai vfolder bulk-delete "${IDS[@]}" >/dev/null

IDS_CSV="$(IFS=,; echo "${IDS[*]}")"

log_step "Verify all targeted vfolders are in a deleted state"
./bai vfolder my-search --limit 500 2>/dev/null \
    | TARGETS="$IDS_CSV" python3 "$SCRIPT_DIR/verify_all_deleted.py" \
    || { log_error "bulk-delete state check failed"; exit 1; }

log_step "Bulk-purge"
./bai vfolder bulk-purge "${IDS[@]}" >/dev/null

# After purge: either gone or delete-complete; must NOT be 'ready'.
log_step "Verify no targeted vfolder is 'ready' after bulk-purge"
./bai vfolder my-search --limit 500 2>/dev/null \
    | TARGETS="$IDS_CSV" python3 "$SCRIPT_DIR/verify_no_ready.py" \
    || { log_error "vfolder still 'ready' after bulk-purge"; exit 1; }

scenario_end_ok
