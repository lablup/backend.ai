#!/bin/bash
# Check that a bake definition's default group covers exactly the publishable
# service images registered in scripts/list-dockerfiles.sh.
#
# Usage:
#   scripts/check-bake-targets.sh <bake-file>
#
# Bake target names cannot contain dots, so docker-bake.hcl names its targets
# backend_ai-<name>; this script maps them back to backend.ai-<name> before
# comparing.  Prints the verified image-name list on success; exits non-zero
# with the drift when the two registries disagree, so a new dockerfile cannot
# be registered for publishing without also being wired into the bake build
# (and vice versa).
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <bake-file>" >&2
  exit 2
fi
bake_file=$1

unset CDPATH
cd -- "$(dirname "$0")/.." >/dev/null

expected=$(scripts/list-dockerfiles.sh --service | jq -r '.include[].name' | LC_ALL=C sort)
actual=$(docker buildx bake --file "$bake_file" --print default 2>/dev/null \
  | jq -r '.group.default.targets[]' \
  | sed 's/^backend_ai-/backend.ai-/' \
  | LC_ALL=C sort)

if [ "$expected" != "$actual" ]; then
  echo "$0: the default group of '$bake_file' and PUBLISHABLE_SERVICES in scripts/list-dockerfiles.sh have drifted:" >&2
  diff --label registered --label baked \
    <(printf '%s\n' "$expected") <(printf '%s\n' "$actual") >&2 || true
  echo "$0: register the image in both places (or remove it from both) to proceed." >&2
  exit 1
fi

printf '%s\n' "$expected"
