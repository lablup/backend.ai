#!/usr/bin/env bash
#
# Write the targets a push checks and tests, and print the file's path.
#
#   plan-push-targets.sh <base-ref> <cache-dir>
#
#     <base-ref>   the revision the push compares against, e.g. origin/main
#     <cache-dir>  the directory that keeps the file, e.g. .pants.d/push-targets
#
# The file lists the changed targets and their direct dependents, one address per
# line. It is named after a hash of <base-ref>'s commit, HEAD's tree and the
# uncommitted changes, so a push of the same content reuses it instead of building
# the dependents map again. A new file replaces the others in <cache-dir>.
#
#   pants --spec-files="$(scripts/plan-push-targets.sh origin/main .pants.d/push-targets)" check
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <base-ref> <cache-dir>" >&2
  exit 1
fi
BASE_REF=$1
CACHE_DIR=$2

key=$(
  {
    git rev-parse "$BASE_REF^{commit}"
    git rev-parse "HEAD^{tree}"
    git diff HEAD
    git ls-files --others --exclude-standard
  } | shasum -a 256 | cut -d' ' -f1
)
file="$CACHE_DIR/$key.txt"
if [ ! -f "$file" ]; then
  mkdir -p "$CACHE_DIR"
  pants --changed-since="$BASE_REF" --changed-dependents=direct list > "$file.tmp"
  find "$CACHE_DIR" -name '*.txt' -delete
  mv "$file.tmp" "$file"
fi
echo "$file"
