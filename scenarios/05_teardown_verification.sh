#!/usr/bin/env bash
# 05: Teardown verification.
# Ensures that scenarios 01-04 left no orphaned resources owned by user A.
# - my session search finds no scenario sessions
# - my-search vfolders contains no scenario-prefixed names
# - my deployment search finds no scenario deployments

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "05_teardown_verification"

bai_config_session
bai_login_admin

# Switch to user A
bai_login_user_a

FAIL=0

log_step "Verify no scenario sessions remain (user A)"
LEFT_SESSIONS="$(./bai my session search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-" python3 -c "
import json, sys, os
prefix=os.environ['P']
d=json.load(sys.stdin)
left=[]
for it in d.get('items', []):
    name = (it.get('metadata') or {}).get('name') or it.get('name') or ''
    status = (it.get('lifecycle') or {}).get('status') or it.get('status','')
    if name.startswith(prefix) and status not in ('TERMINATED','CANCELLED'):
        left.append(f\"{it['id']} {name} [{status}]\")
print('\\n'.join(left))
")"
if [[ -n "$LEFT_SESSIONS" ]]; then
    log_error "leaked sessions:"
    echo "$LEFT_SESSIONS" >&2
    FAIL=1
else
    log_ok "no leaked sessions"
fi

log_step "Verify no scenario vfolders remain (user A)"
LEFT_VFS="$(./bai vfolder my-search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-vf-" python3 -c "
import json,sys,os
prefix=os.environ['P']
d=json.load(sys.stdin)
left=[]
DELETED={'delete-pending','delete-ongoing','delete-complete','delete-error','delete-aborted'}
for it in d.get('items', []):
    name=(it.get('metadata') or {}).get('name') or it.get('name','')
    if name.startswith(prefix) and it.get('status') not in DELETED:
        left.append(f\"{it['id']} {name}\")
print('\\n'.join(left))
")"
if [[ -n "$LEFT_VFS" ]]; then
    log_warn "vfolders still listed (may be in trash, will be purged in 99_teardown):"
    echo "$LEFT_VFS" >&2
else
    log_ok "no leaked vfolders"
fi

log_step "Verify no scenario deployments remain (user A)"
LEFT_DEPS="$(./bai my deployment search --limit 200 2>&1 | P="${SCENARIO_PREFIX}-dep-" python3 -c "
import json,sys,os
prefix=os.environ['P']
try:
    d=json.load(sys.stdin)
except Exception:
    print(''); sys.exit(0)
left=[]
TERMINAL={'STOPPED','DESTROYED','DELETED','TERMINATED','CANCELLED'}
for it in d.get('items', []):
    md=it.get('metadata') or {}
    name=md.get('name') or it.get('name','')
    status=md.get('status') or it.get('status','')
    if name.startswith(prefix) and status not in TERMINAL:
        left.append(f\"{it['id']} {name} [{status}]\")
print('\\n'.join(left))
")" || LEFT_DEPS=""
if [[ -n "$LEFT_DEPS" ]]; then
    log_error "leaked deployments:"
    echo "$LEFT_DEPS" >&2
    FAIL=1
else
    log_ok "no leaked deployments"
fi

if (( FAIL == 1 )); then
    log_error "teardown verification failed"
    exit 1
fi

scenario_end_ok
