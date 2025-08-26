#!/usr/bin/env bash
set -euo pipefail
PYVER="3.13.7"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv_init_script="export PATH=\"\$HOME/.local/bin:\$PATH\""
  append_to_profiles "$uv_init_script"
  eval "$uv_init_script"
fi
# This variant transparently runs the python command without creating virtualenvs.
# e.g., `scripts/python.sh -c '...'`
uv run --python="${PYVER}" --no-project python "$@"
