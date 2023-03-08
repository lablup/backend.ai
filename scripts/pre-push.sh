# implementation: backend.ai monorepo standard pre-push hook
BASE_PATH=$(pwd)
if [ -f "$BASE_PATH/pants-local" ]; then
  PANTS="$BASE_PATH/pants-local"
else
  PANTS="$BASE_PATH/pants"
fi
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ -n "$(echo "$CURRENT_BRANCH" | sed -n '/[[:digit:]]\{1,\}\.[[:digit:]]\{1,\}/p')" ]; then
  # if we are on the release branch, use it as the base branch.
  BASE_BRANCH="$CURRENT_BRANCH"
else
  BASE_BRANCH="main"
fi
if [ "$1" != "origin" ]; then
  # extract the owner name of the target repo
  ORIGIN="$(echo "$1" | grep -o '://[^/]\+/[^/]\+/' | grep -o '/[^/]\+/$' | tr -d '/')"
  cleanup_remote() {
    git remote remove "$ORIGIN"
  }
  trap cleanup_remote EXIT
  git remote add "$ORIGIN" "$1"
  git fetch -q --depth=1 --no-tags "$ORIGIN" "$BASE_BRANCH"
else
  ORIGIN="origin"
fi
echo "Performing lint and check on ${ORIGIN}/${BASE_BRANCH}..HEAD@${CURRENT_COMMIT} ..."
"$PANTS" tailor --check update-build-files --check ::
"$PANTS" lint check --changed-since="${ORIGIN}/${BASE_BRANCH}"
