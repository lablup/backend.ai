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

cd "$(git rev-parse --show-toplevel)"

PY_FILES=()
while IFS= read -r -d '' f; do
  PY_FILES+=("$f")
done < <(git diff --cached --name-only --diff-filter=ACMR -z -- '*.py' '*.pyi')

if [ ${#PY_FILES[@]} -eq 0 ]; then
  echo "No staged Python files; skipping ruff."
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv is not installed. Install it (https://docs.astral.sh/uv/) to run the pre-commit ruff checks." >&2
  exit 1
fi

RUFF_VERSION=$(scripts/pyscript.sh scripts/tomltool.py -f pants.toml get 'ruff.version')
RUFF=(uvx "ruff@${RUFF_VERSION}")

EXIT_CODE=0

echo "Running pre-commit checks (ruff ${RUFF_VERSION})..."

# 1. Auto-format
echo "✓ Formatting..."
if ! "${RUFF[@]}" format --force-exclude "${PY_FILES[@]}"; then
  echo "❌ Formatting failed"
  EXIT_CODE=1
fi

# 2. Linting
echo "✓ Linting..."
if ! "${RUFF[@]}" check --force-exclude "${PY_FILES[@]}"; then
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
