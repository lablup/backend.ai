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
done < <(git diff --cached --name-only --diff-filter=ACMR -z -- '*.py' '*.pyi' 'BUILD' '*/BUILD')

if [ ${#PY_FILES[@]} -eq 0 ]; then
  echo "No staged Python or BUILD files; skipping ruff."
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv is not installed. Install it (https://docs.astral.sh/uv/) to run the pre-commit ruff checks." >&2
  exit 1
fi

# ruff from the `lint` group of pyproject.toml, in a gitignored venv
install_lint_venv() {
  uv venv --quiet --allow-existing dist/lint-venv
  uv pip install --quiet --python dist/lint-venv --group pyproject.toml:lint
}
install_lint_venv
RUFF=(dist/lint-venv/bin/ruff)

EXIT_CODE=0

echo "Running pre-commit checks ($("${RUFF[@]}" --version))..."

# 1. Auto-format
echo "✓ Formatting..."
if ! "${RUFF[@]}" format --check --force-exclude "${PY_FILES[@]}"; then
  "${RUFF[@]}" format --force-exclude "${PY_FILES[@]}" || true
  echo "❌ Files were reformatted. Review the changes, stage them with git add and commit again."
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
