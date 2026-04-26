#!/usr/bin/env bash
# 12: VFolder file I/O — round-trip a real file through storage-proxy via TUS.
# - Create vfolder
# - `vfolder upload` returns a TUS token+URL → PATCH file body via curl
# - `vfolder ls` shows the new file with the right size
# - `vfolder download` returns a download token+URL → GET file via curl
# - Downloaded bytes match the uploaded payload

set -euo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

scenario_begin "12_vfolder_file_io"

bai_config_session
bai_login_admin
bai_login_user_a

VF_NAME="${SCENARIO_PREFIX}-vf-fileio-$$"
LOCAL_FILE="$SCENARIO_TMP_DIR/payload-${VF_NAME}.txt"
DOWNLOAD_FILE="$SCENARIO_TMP_DIR/payload-${VF_NAME}.downloaded"
REMOTE_NAME="$(basename "$LOCAL_FILE")"

# Use a payload that is non-trivial but small enough to fit in a single chunk.
python3 -c "
import os, sys
# 4 KiB of deterministic content
data = (b'hello-scenario-fileio\n' * 200)[:4096]
sys.stdout.buffer.write(data)
" > "$LOCAL_FILE"
SIZE="$(wc -c < "$LOCAL_FILE" | tr -d ' ')"
log_step "Prepared local payload: ${LOCAL_FILE} (${SIZE} bytes)"

log_step "Create vfolder '${VF_NAME}'"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed"; exit 1; }
log_ok "$VF_ID"

# --- Upload via TUS PATCH ---
log_step "Get upload session token from manager"
UP_RESP="$(./bai vfolder upload "$VF_ID" "$LOCAL_FILE" 2>&1)"
UP_TOKEN="$(echo "$UP_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")"
UP_URL="$(echo "$UP_RESP"   | python3 -c "import json,sys; print(json.load(sys.stdin)['url'])")"
[[ -n "$UP_TOKEN" && -n "$UP_URL" ]] || { log_error "missing upload token/url"; echo "$UP_RESP" >&2; exit 1; }
log_ok "tus url: ${UP_URL}"

log_step "PATCH payload via TUS protocol"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' \
    -X PATCH "${UP_URL}?token=${UP_TOKEN}" \
    -H "Tus-Resumable: 1.0.0" \
    -H "Upload-Offset: 0" \
    -H "Content-Type: application/offset+octet-stream" \
    --data-binary "@${LOCAL_FILE}")"
[[ "$HTTP_CODE" == "204" ]] || { log_error "TUS PATCH failed: HTTP $HTTP_CODE"; exit 1; }
log_ok "HTTP 204 No Content"

# --- Verify file is visible via vfolder ls ---
# Note: storage proxy rejects "/" and "." as path; use empty string for root.
log_step "Verify file visible via 'vfolder ls' (root)"
LS_OUT="$(./bai vfolder ls "$VF_ID" "" 2>&1)"
echo "$LS_OUT" | NAME="$REMOTE_NAME" SIZE="$SIZE" python3 -c "
import json, sys, os
target = os.environ['NAME']
expected = int(os.environ['SIZE'])
d = json.load(sys.stdin)
items = d.get('items') or d.get('files') or d
if isinstance(items, dict):
    items = items.get('items') or []
for it in items:
    name = it.get('name') or it.get('filename') or ''
    if name == target:
        size = it.get('size')
        if size is None or int(size) != expected:
            print(f'SIZE_MISMATCH expected={expected} got={size}'); sys.exit(1)
        print('OK'); sys.exit(0)
print('NOT_FOUND'); sys.exit(1)
" || { log_error "uploaded file not visible / size mismatch"; echo "$LS_OUT" >&2; exit 1; }
log_ok "file present with size ${SIZE}"

# --- Download via GET ---
log_step "Get download session token from manager"
DL_RESP="$(./bai vfolder download "$VF_ID" "$REMOTE_NAME" 2>&1)"
DL_TOKEN="$(echo "$DL_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")"
DL_URL="$(echo "$DL_RESP"   | python3 -c "import json,sys; print(json.load(sys.stdin)['url'])")"
[[ -n "$DL_TOKEN" && -n "$DL_URL" ]] || { log_error "missing download token/url"; echo "$DL_RESP" >&2; exit 1; }
log_ok "dl url: ${DL_URL}"

log_step "GET file via download URL"
HTTP_CODE="$(curl -s -o "$DOWNLOAD_FILE" -w '%{http_code}' \
    "${DL_URL}?token=${DL_TOKEN}")"
[[ "$HTTP_CODE" == "200" ]] || { log_error "download failed: HTTP $HTTP_CODE"; exit 1; }

log_step "Compare uploaded and downloaded bytes"
UP_HASH="$(shasum -a 256 "$LOCAL_FILE"    | awk '{print $1}')"
DN_HASH="$(shasum -a 256 "$DOWNLOAD_FILE" | awk '{print $1}')"
if [[ "$UP_HASH" != "$DN_HASH" ]]; then
    log_error "hash mismatch: upload=${UP_HASH} download=${DN_HASH}"
    exit 1
fi
log_ok "round-trip sha256 match: $UP_HASH"

log_step "Cleanup"
./bai vfolder delete "$VF_ID" >/dev/null
./bai vfolder purge  "$VF_ID" >/dev/null
rm -f "$LOCAL_FILE" "$DOWNLOAD_FILE"

scenario_end_ok
