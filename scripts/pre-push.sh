# backend.ai monorepo standard pre-push hook
BASE_PATH=$(cd "$(dirname "$0")"/../.. && pwd)
if [ -f "$BASE_PATH/pants-local" ]; then
  PANTS="$BASE_PATH/pants-local"
else
  PANTS="$BASE_PATH/pants"
fi
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ -n "$(echo "$CURRENT_BRANCH" | sed -n '/^[0-9]\+\.[0-9]\+$/p')" ]; then
  # if we are on the release branch, use it as the base branch.
  BASE_BRANCH="$CURRENT_BRANCH"
else
  BASE_BRANCH="main"
fi
echo "Performing lint and check on $1/${BASE_BRANCH}..HEAD@${CURRENT_COMMIT} ..."
"$PANTS" tailor --check update-build-files --check
"$PANTS" lint check --changed-since="$1/${BASE_BRANCH}"
