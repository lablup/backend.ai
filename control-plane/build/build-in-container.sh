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

BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
COMMIT=$(git -C "$REPO" rev-parse HEAD)
PENDING=$(git -C "$REPO" status --porcelain -- control-plane credential-broker)
if [ -n "$PENDING" ]; then
    if [ -z "${BAI_ALLOW_UNCOMMITTED:-}" ]; then
        echo "build-in-container: the bundle sources are uncommitted, so the measured image could not be attributed to a revision:" >&2
        echo "$PENDING" >&2
        exit 1
    fi
    COMMIT="${COMMIT}-uncommitted"
fi
CARRIED=$(mktemp)
trap 'rm -f "$CARRIED"' EXIT
git -C "$REPO" log --format='%s' HEAD -- control-plane credential-broker | sort -u > "$CARRIED"
UNMERGED=$(git -C "$REPO" for-each-ref --format='%(refname:short)' refs/heads |
    while read -r ref; do
        git -C "$REPO" log --cherry-pick --right-only --no-merges --format="${ref}%x09%h%x09%s" \
            "HEAD...${ref}" -- control-plane credential-broker
    done | sort -u |
    while IFS=$'\t' read -r ref short subject; do
        grep -Fxq "$subject" "$CARRIED" || printf '%s %s %s\n' "$ref" "$short" "$subject"
    done)
[ -z "$UNMERGED" ] ||
    echo "build-in-container: branches carry bundle commits this image will not:" >&2
[ -z "$UNMERGED" ] || echo "$UNMERGED" >&2

$DOCKER run --rm --privileged \
    -v "${REPO}:${REPO}" -v "${OUT}:${OUT}" \
    -e "BACKENDAI_KBS_URL=${BACKENDAI_KBS_URL:?BACKENDAI_KBS_URL must be set}" \
    -e "BAI_REUSE_ROOTFS=${BAI_REUSE_ROOTFS:-}" \
    -e "BAI_SOURCE_BRANCH=${BRANCH}" -e "BAI_SOURCE_COMMIT=${COMMIT}" \
    -e "BAI_UNMERGED_BUNDLE_COMMITS=${UNMERGED}" \
    "$IMAGE" "${HERE}/build-state-bundle.sh" "${OUT}/bundle" "${inputs[@]}"
