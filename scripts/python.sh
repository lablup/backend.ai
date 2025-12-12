#!/usr/bin/env bash
set -euo pipefail
PYVER="3.14.2"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if [ $SHELL = "/bin/fish" ]; then
    source $HOME/.local/bin/env.fish
  else
    source $HOME/.local/bin/env
  fi
fi
# This variant transparently runs the python command without creating virtualenvs.
# e.g., `scripts/python.sh -c '...'`
uv run --python="${PYVER}" --no-project python "$@"
