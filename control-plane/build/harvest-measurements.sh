#!/bin/bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
BUNDLE=${1:?usage: harvest-measurements.sh <bundle-dir> <broker-state-dir> <output-dir>}
BROKER=${2:?broker state directory holding the attestation-service policies}
OUT=${3:?output directory for the decoy disk and decoy broker state}

REPO='default\x2Fcontrol-plane'

rm -rf "$OUT"
install -d -m 0700 "$OUT"
install -d -m 0755 "${OUT}/storage/repository" "${OUT}/storage/kbs"

cp "${BUNDLE}/state-header-mac" "${OUT}/production-header-mac"

head -c 32 /dev/urandom > "${OUT}/decoy-disk-key"
chmod 0600 "${OUT}/decoy-disk-key"

"${HERE}/assemble-disk.sh" "$BUNDLE" "${OUT}/harvest-disk.img" "${OUT}/decoy-disk-key" "${BAI_STATE_MIB:-8192}"

cp -a "${BROKER}/storage/attestation_service_policy" "${OUT}/storage/"
cp "${OUT}/decoy-disk-key" "${OUT}/storage/repository/${REPO}\\x2Fstate-disk-key"
tr -d ' \n\r' < "${BUNDLE}/state-header-mac" \
    > "${OUT}/storage/repository/${REPO}\\x2Fstate-header-mac"

cp "${OUT}/production-header-mac" "${BUNDLE}/state-header-mac"

cat > "${OUT}/storage/kbs/resource-policy.rego" <<'REGO'
package policy

import rego.v1

default allow = false

allow if {
    body := input.submods.cpu0["ear.veraison.annotated-evidence"].tdx.quote.body
    count(body.mr_td) == 96
    count(body.rtmr_1) == 96
}
REGO

echo "harvest-measurements: decoy broker state under ${OUT}/storage carries only"
find "${OUT}/storage/repository" -type f -printf '  %f\n'
echo "harvest-measurements: serve that storage at the measured broker URL, boot"
echo "  ${OUT}/harvest-disk.img, and read the measurements the credential broker prints"
