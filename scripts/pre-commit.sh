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

GO_EXIT=0
GO_FILES=()
while IFS= read -r -d '' f; do
  GO_FILES+=("$f")
done < <(git diff --cached --name-only --diff-filter=ACMR -z -- '*.go')

if [ ${#GO_FILES[@]} -eq 0 ]; then
  echo "No staged Go files; skipping golangci-lint."
else
  echo "Running Go pre-commit checks..."
  echo "✓ Formatting Go..."
  if ! go tool golangci-lint fmt --diff "${GO_FILES[@]}" >/dev/null; then
    go tool golangci-lint fmt "${GO_FILES[@]}" || true
    echo "❌ Go files were reformatted. Review the changes, stage them with git add and commit again."
    GO_EXIT=1
  fi
  echo "✓ Linting Go..."
  if ! go tool golangci-lint run --fast-only --new-from-rev HEAD; then
    echo "❌ Go linting failed"
    GO_EXIT=1
  fi
fi

exit "$GO_EXIT"
