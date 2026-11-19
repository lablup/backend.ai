#!/usr/bin/env bash
#
# Print the Python files to type-check, one per line.
#
#   list-typecheck-files.sh <targets-file>
#
#     <targets-file>  `typecheck.txt`: a file path or an address per line
#
# Drops what follows `:` in a line, then the duplicates, the lines that are not
# `.py` or `.pyi` and the files that no longer exist. Prints nothing when none is left.
set -e

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <targets-file>" >&2
  exit 2
fi

while IFS= read -r line; do
  path="${line%%:*}"
  case "$path" in
    *.py|*.pyi) if [ -f "$path" ]; then echo "$path"; fi ;;
  esac
done < "$1" | sort -u
