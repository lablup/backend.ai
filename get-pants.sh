#!/usr/bin/env bash
# pantsbuild/actions/init-pants runs this instead of the upstream get-pants.sh.
# Runs the same upstream script, retrying it because the launcher download returns 504 intermittently.
set -euo pipefail

# The latest upstream script, the same URL scripts/install-dev.sh uses.
script=$(mktemp)
curl --proto '=https' --tlsv1.2 -fsSL --retry 5 --retry-all-errors --retry-delay 5 -o "$script" \
  https://static.pantsbuild.org/setup/get-pants.sh

for attempt in 1 2 3 4 5 6; do
  if bash "$script" "$@"; then
    exit 0
  fi
  echo "get-pants.sh failed (attempt ${attempt}/6)" >&2
  if [ "$attempt" -lt 6 ]; then
    sleep $((attempt * 10))
  fi
done
exit 1
