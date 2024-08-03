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

if ! command -v gh &> /dev/null; then
  echo "GitHub CLI (gh) is not installed. Since we cannot determine the base branch, running the full check before push."
  pants tailor --check update-build-files --check ::
  pants lint check ::
else
  # Get the base branch name from GitHub if we are on a pull request.
  if gh pr view "$CURRENT_BRANCH" &> /dev/null; then
    BASE_BRANCH=$(gh pr view "$CURRENT_BRANCH" --json baseRefName -q '.baseRefName')
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
fi
