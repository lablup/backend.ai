#!/usr/bin/env bash
# Fails when the index of the repository holds a file whose name matches one of
# the patterns, in any directory.
#
# Usage: check-removed-files.sh <file name pattern>...
# Example: check-removed-files.sh '*.py' 'BUILD'
#
# Prints each matching file and exits 1; prints nothing and exits 0 when no file
# matches.
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <file name pattern>..." >&2
  exit 2
fi

pathspecs=()
for pattern in "$@"; do
  pathspecs+=(":(top,glob)**/${pattern}")
done

found=$(git ls-files --full-name -- "${pathspecs[@]}")

if [ -n "$found" ]; then
  echo "Files removed from this branch are present again:" >&2
  echo "$found" >&2
  exit 1
fi
