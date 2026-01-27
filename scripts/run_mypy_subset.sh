#!/bin/bash
#
# Run mypy type checking on a subset of files.
#
# This script runs mypy (via pants check) on specific paths to validate
# type checking compliance during incremental linter rule enablement.
#
# Usage:
#     ./scripts/run_mypy_subset.sh <path>
#
# Where <path> can be:
#     - A single Python file
#     - A directory (will check all Python files recursively)
#
# Examples:
#     ./scripts/run_mypy_subset.sh src/ai/backend/web/
#     ./scripts/run_mypy_subset.sh src/ai/backend/common/types.py

set -e

if [ $# -eq 0 ]; then
    echo "Error: No path specified" >&2
    echo "Usage: $0 <path>" >&2
    exit 1
fi

PATH_TO_CHECK="$1"

# Check if path exists
if [ ! -e "$PATH_TO_CHECK" ]; then
    echo "Error: Path does not exist: $PATH_TO_CHECK" >&2
    exit 1
fi

# Find project root (directory containing pyproject.toml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "Error: Could not find project root (pyproject.toml)" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

# Convert path to relative if it's absolute
if [[ "$PATH_TO_CHECK" = /* ]]; then
    PATH_TO_CHECK="${PATH_TO_CHECK#$PROJECT_ROOT/}"
fi

echo "Running mypy type check on: $PATH_TO_CHECK"
echo ""

# Run pants check with no colors and no dynamic UI for clean output
pants --no-colors --no-dynamic-ui check "$PATH_TO_CHECK"::