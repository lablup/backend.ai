#!/usr/bin/env bash
set -euo pipefail
PYVER="3.13.7"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if [ $SHELL = "/bin/fish" ]; then
    source $HOME/.local/bin/env.fish
  else
    source $HOME/.local/bin/env
  fi
fi
# This variant auto-manages the script dependency caches in ~/.cache/uv and run the script using the cached venv.
# e.g., `scripts/pyscript.sh scripts/do-something.py ...`
uv run --python="${PYVER}" --no-project --script "$@"
