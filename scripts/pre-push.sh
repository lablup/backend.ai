#! /bin/bash
# implementation: backend.ai monorepo standard pre-push hook
BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
if [ -f .pants.rc ]; then
  source scripts/bootstrap-static-python.sh
  local_exec_root_dir=$($bpython scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')
  mkdir -p "$local_exec_root_dir"
fi
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ -n "$(echo "$CURRENT_BRANCH" | sed -n '/^[[:digit:]]\{1,\}\.[[:digit:]]\{1,\}/p')" ]; then
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
pants tailor --check update-build-files --check ::
pants lint check --changed-since="${ORIGIN}/${BASE_BRANCH}"
