# backend.ai monorepo standard pre-commit hook
BASE_PATH=$(cd "$(dirname "$0")"/../.. && pwd)
if [ -f "$BASE_PATH/pants-local" ]; then
  PANTS="$BASE_PATH/pants-local"
else
  PANTS="$BASE_PATH/pants"
fi
echo "Performing lint for changed files ..."
"$PANTS" lint --changed-since="HEAD~1"
