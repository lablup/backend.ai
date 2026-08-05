#!/bin/bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "${HERE}/../.." && pwd)
IMAGE=${BAI_BUILDER_IMAGE:-bai-state-bundle-builder:1}
DOCKER=${DOCKER:-docker}
OUT=${1:?usage: build-in-container.sh <output-dir> <manager> <coordinator> <kbs-client>}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
shift

$DOCKER image inspect "$IMAGE" >/dev/null 2>&1 ||
    $DOCKER build -t "$IMAGE" -f "${HERE}/Dockerfile.builder" "$HERE"

mkdir -p "${OUT}/inputs"
inputs=()
for path in "$@"; do
    install -m 0755 "$path" "${OUT}/inputs/$(basename "$path")"
    inputs+=("${OUT}/inputs/$(basename "$path")")
done

$DOCKER run --rm --privileged \
    -v "${REPO}:${REPO}" -v "${OUT}:${OUT}" \
    -e "BACKENDAI_KBS_URL=${BACKENDAI_KBS_URL:?BACKENDAI_KBS_URL must be set}" \
    -e "BAI_REUSE_ROOTFS=${BAI_REUSE_ROOTFS:-}" \
    "$IMAGE" "${HERE}/build-state-bundle.sh" "${OUT}/bundle" "${inputs[@]}"
