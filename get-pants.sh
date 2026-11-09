#!/usr/bin/env bash
# pantsbuild/actions/init-pants runs this instead of the upstream get-pants.sh.
# Runs the same upstream script, retrying it because the launcher download returns 504 intermittently.
set -euo pipefail

# The setup-commit that init-pants v11 pins.
commit=6f136713a46e555946a22ffb3ed49c372eea58df
script=$(mktemp)
curl --proto '=https' --tlsv1.2 -fsSL --retry 5 --retry-all-errors --retry-delay 5 -o "$script" \
  "https://raw.githubusercontent.com/pantsbuild/setup/${commit}/get-pants.sh"

for attempt in 1 2 3 4 5; do
  if bash "$script" "$@"; then
    exit 0
  fi
  echo "get-pants.sh failed (attempt ${attempt}/5)" >&2
  sleep 5
done
exit 1
