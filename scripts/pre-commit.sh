#! /bin/bash

# Make it interruptible.
PGID="$(ps -o pgid= $$ | tr -d ' ')"
cleanup() {
  local sig="$1"
  trap - SIGINT SIGTERM
  echo -e "Pre-commit hook is interrupted ($sig)." >&2
  kill -s "${sig}" -- "-${PGID}"
}
trap 'cleanup INT' SIGINT
trap 'cleanup TERM' SIGTERM

# --- Hook Body ---
set -Eeuo pipefail

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
cd "$BASE_PATH"

# Setup pants local execution directory
if [ -f .pants.rc ]; then
  local_exec_root_dir=$(scripts/pyscript.sh scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')
  mkdir -p "$local_exec_root_dir"
fi

EXIT_CODE=0

echo "Running pre-commit checks..."

# 1. Auto-format
echo "✓ Formatting..."
if ! pants fmt --changed-since="HEAD"; then
  echo "❌ Formatting failed"
  EXIT_CODE=1
fi

# 2. Linting
echo "✓ Linting..."
if ! pants lint --changed-since="HEAD"; then
  echo "❌ Linting failed"
  EXIT_CODE=1
fi

if [ $EXIT_CODE -ne 0 ]; then
  echo ""
  echo "❌ Pre-commit checks failed. Please fix the issues above."
  exit $EXIT_CODE
fi

echo ""
echo "✅ All pre-commit checks passed"
exit 0
