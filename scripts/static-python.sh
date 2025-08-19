#!/usr/bin/env bash
set -euo pipefail
PYVER="3.13.7"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
uv run --python="${PYVER}" --script "$@"
