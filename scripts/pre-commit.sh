# backend.ai monorepo standard pre-commit hook
BASE_PATH=$(cd "$(dirname "$0")"/../.. && pwd)
if [ -f "$BASE_PATH/pants-local" ]; then
  PANTS="$BASE_PATH/pants-local"
else
  PANTS="$BASE_PATH/pants"
fi
"$PANTS" fmt --changed-since="HEAD~1"
