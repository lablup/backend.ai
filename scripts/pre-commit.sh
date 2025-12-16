#! /bin/bash
# implementation: backend.ai monorepo standard pre-commit hook
set -e  # Exit on error

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
cd "$BASE_PATH"

# Setup pants local execution directory
if [ -f .pants.rc ]; then
  local_exec_root_dir=$(scripts/pyscript.sh scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')
  mkdir -p "$local_exec_root_dir"
fi

EXIT_CODE=0

# 1. Linting
echo "Running pre-commit checks..."
echo "✓ Linting..."
if ! pants lint --changed-since="HEAD"; then
  echo "❌ Linting failed"
  EXIT_CODE=1
fi

# 2. Type checking
echo "✓ Type checking..."
if ! pants check --changed-since="HEAD"; then
  echo "❌ Type checking failed"
  EXIT_CODE=1
fi

# 3. Direct tests (only tests that were directly changed)
echo "✓ Testing changed files..."
if ! pants test --changed-since="HEAD"; then
  echo "❌ Tests failed"
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
