#! /bin/bash
# Runs ruff at the version pyproject.toml pins (`[tool.ruff] required-version`) through uvx.
# Usage: scripts/ruff.sh <ruff arguments>
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC=$("$ROOT/scripts/pyscript.sh" "$ROOT/scripts/tomltool.py" -f "$ROOT/pyproject.toml" get tool.ruff.required-version)
exec uvx "ruff${SPEC}" "$@"
