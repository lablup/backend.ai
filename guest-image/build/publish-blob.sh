#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need sha256sum sed tr install

image_digest="${1:?usage: publish-blob.sh <image-config-digest> [blob-file]}"
blob="${2:-}"
store="${BAI_CC_BLOB_STORE:-/var/lib/backend.ai/coco-blobs}"

if [ -z "$blob" ]; then
	[ -r "${BAI_CC_OUT}/mr_config_id.txt" ] || die "no mr_config_id.txt under ${BAI_CC_OUT}; run 'make blob' first"
	blob="${BAI_CC_OUT}/initdata/$(tr -d '[:space:]' < "${BAI_CC_OUT}/mr_config_id.txt").b64"
fi
[ -s "$blob" ] || die "$blob is empty or missing"

slug() { printf '%s' "$1" | sed 's/[^0-9a-zA-Z][^0-9a-zA-Z]*/-/g' | tr '[:upper:]' '[:lower:]'; }

address="sha256:$(sha256_of "$blob")"
install -D -m 0444 "$blob" "${store}/blobs/$(slug "$address")"
index="${store}/by-image/$(slug "$image_digest")"
mkdir -p "$(dirname "$index")"
printf "%s" "$address" > "$index"
chmod 0644 "$index"

readback="$(cat "$index")"
[ "$readback" = "$address" ] || die "index $index reads back as $readback, not $address"
verify="sha256:$(sha256_of "${store}/blobs/$(slug "$address")")"
[ "$verify" = "$address" ] || die "published blob hashes to $verify, indexed as $address"

log "published $blob"
log "  content address $address"
log "  image digest    $image_digest"
log "  index           $index"
