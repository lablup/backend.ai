#!/bin/sh
# Build (and optionally push) the krunner image.
# Usage: deploy/krunner/build.sh <image-ref> [--push]
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
IMAGE=$1
PYTHON=${PYTHON:-$(ls -d "$ROOT"/dist/export/python/virtualenvs/python-default/*/bin/python | tail -1)}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

KRUNNER=$("$PYTHON" -c 'import ai.backend.krunner, os; print(os.path.dirname(ai.backend.krunner.__path__[0] + "/x"))')
CTX=$WORK/context
mkdir -p "$CTX"
cp "$KRUNNER"/static_gnu/krunner-env.static-gnu.x86_64.tar.xz "$CTX/krunner-env.static-gnu.tar.xz"
cp "$KRUNNER"/static_gnu/krunner-python.static-gnu.txt "$CTX/krunner-python.static-gnu.txt"
cp "$KRUNNER"/alpine/krunner-env.musllinux_1_2.x86_64.tar.xz "$CTX/krunner-env.musllinux.tar.xz"
cp "$KRUNNER"/alpine/krunner-python.musllinux_1_2.txt "$CTX/krunner-python.musllinux.txt"
cp -a "$ROOT/src/ai/backend/runner" "$CTX/runner"
cp -a "$ROOT/src/ai/backend/kernel" "$CTX/kernel"
cp -a "$ROOT/src/ai/backend/helpers" "$CTX/helpers"
cp "$ROOT/deploy/krunner/Dockerfile" "$ROOT/deploy/krunner/install.sh" "$WORK/"

docker build -t "$IMAGE" "$WORK"
if [ "${2:-}" = "--push" ]; then
  docker push "$IMAGE"
fi
