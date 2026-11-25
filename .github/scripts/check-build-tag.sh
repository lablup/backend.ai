#!/usr/bin/env bash
# Fails when a package matching the pattern holds a Go file that the default
# build selects, that is, a file without the build tag the pattern's files must
# carry. The tag is the one `go list` is not given, so no tag is passed here.
#
# Usage: check-build-tag.sh <package pattern>
# Example: check-build-tag.sh './tests/integration/...'
#
# Prints each offending package with its file counts and exits 1; prints
# nothing and exits 0 when every Go file is left out of the default build.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	echo "usage: $0 <package pattern>" >&2
	exit 2
fi

offenders=$(
	go list -e -f '{{.ImportPath}} {{len .GoFiles}} {{len .TestGoFiles}} {{len .XTestGoFiles}}' "$1" |
		awk '$2 + $3 + $4 > 0 { print $1 " (files: " $2 ", test files: " $3 ", external test files: " $4 ")" }'
)

if [ -n "$offenders" ]; then
	echo "Go files without the build tag in the default build:" >&2
	echo "$offenders" >&2
	exit 1
fi
