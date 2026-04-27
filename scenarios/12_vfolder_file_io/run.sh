#!/usr/bin/env bash
# 12: TUS upload → ls → download → sha256 round-trip via storage-proxy.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
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

python3 "$SCRIPT_DIR/gen_payload.py" > "$LOCAL_FILE"
SIZE="$(wc -c < "$LOCAL_FILE" | tr -d ' ')"

log_step "Create vfolder '${VF_NAME}' (payload ${SIZE} bytes)"
./bai vfolder create --name "$VF_NAME" --host "$TEST_VFOLDER_HOST" >/dev/null
VF_ID="$(lookup_my_vfolder_id "$VF_NAME")"
[[ -n "$VF_ID" ]] || { log_error "vfolder lookup failed"; exit 1; }

log_step "Get TUS upload token"
UP_RESP="$(./bai vfolder upload "$VF_ID" "$LOCAL_FILE" 2>&1)"
UP_TOKEN="$(printf '%s' "$UP_RESP" | FIELD=token python3 "$SCN_PY/print_json_field.py")"
UP_URL="$(printf '%s' "$UP_RESP"   | FIELD=url   python3 "$SCN_PY/print_json_field.py")"
[[ -n "$UP_TOKEN" && -n "$UP_URL" ]] || { log_error "missing upload token/url: $UP_RESP"; exit 1; }

log_step "PATCH payload via TUS"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' \
    -X PATCH "${UP_URL}?token=${UP_TOKEN}" \
    -H "Tus-Resumable: 1.0.0" \
    -H "Upload-Offset: 0" \
    -H "Content-Type: application/offset+octet-stream" \
    --data-binary "@${LOCAL_FILE}")"
[[ "$HTTP_CODE" == "204" ]] || { log_error "TUS PATCH failed: HTTP $HTTP_CODE"; exit 1; }

# Storage proxy rejects '/' or '.' as path; use empty string for root.
log_step "Verify file visible via 'vfolder ls' with correct size"
./bai vfolder ls "$VF_ID" "" 2>&1 \
    | NAME="$REMOTE_NAME" SIZE="$SIZE" python3 "$SCRIPT_DIR/verify_file_size.py" \
    || { log_error "uploaded file not visible / size mismatch"; exit 1; }

log_step "Get download token + GET file"
DL_RESP="$(./bai vfolder download "$VF_ID" "$REMOTE_NAME" 2>&1)"
DL_TOKEN="$(printf '%s' "$DL_RESP" | FIELD=token python3 "$SCN_PY/print_json_field.py")"
DL_URL="$(printf '%s' "$DL_RESP"   | FIELD=url   python3 "$SCN_PY/print_json_field.py")"
[[ -n "$DL_TOKEN" && -n "$DL_URL" ]] || { log_error "missing download token/url: $DL_RESP"; exit 1; }

HTTP_CODE="$(curl -s -o "$DOWNLOAD_FILE" -w '%{http_code}' "${DL_URL}?token=${DL_TOKEN}")"
[[ "$HTTP_CODE" == "200" ]] || { log_error "download failed: HTTP $HTTP_CODE"; exit 1; }

log_step "Compare sha256(uploaded) == sha256(downloaded)"
UP_HASH="$(shasum -a 256 "$LOCAL_FILE"    | awk '{print $1}')"
DN_HASH="$(shasum -a 256 "$DOWNLOAD_FILE" | awk '{print $1}')"
[[ "$UP_HASH" == "$DN_HASH" ]] || { log_error "hash mismatch: upload=${UP_HASH} download=${DN_HASH}"; exit 1; }
log_ok "round-trip sha256: $UP_HASH"

log_step "Cleanup"
./bai vfolder delete "$VF_ID" >/dev/null
./bai vfolder purge  "$VF_ID" >/dev/null
rm -f "$LOCAL_FILE" "$DOWNLOAD_FILE"

scenario_end_ok
