#! /bin/bash

# Make it interruptible.
PGID="$(ps -o pgid= $$ | tr -d ' ')"
cleanup() {
  local sig="$1"
  trap - SIGINT SIGTERM
  echo -e "\nPre-push hook is interrupted ($sig)." >&2
  kill -s "${sig}" -- "-${PGID}"
}
trap 'cleanup INT' SIGINT
trap 'cleanup TERM' SIGTERM

# --- Hook Body ---
set -Eeuo pipefail

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if ! command -v gh &> /dev/null; then
  echo "GitHub CLI (gh) is not installed. Checking words against HEAD~1."
  python3 scripts/knowledge/check_words.py --base HEAD~1
  exit 0
fi

# Get the base branch name from GitHub if we are on a pull request.
BASE_BRANCH=$(gh pr view "$CURRENT_BRANCH" --json baseRefName -q '.baseRefName' 2>/dev/null || true)
if [[ -z "$BASE_BRANCH" ]]; then
  if [ -n "$(echo "$CURRENT_BRANCH" | sed -n '/^[[:digit:]]\{1,\}\.[[:digit:]]\{1,\}/p')" ]; then
    # if we are on the release branch, use it as the base branch.
    echo "We are on a release branch $CURRENT_BRANCH."
    BASE_BRANCH="$CURRENT_BRANCH"
  else
    echo "No pull request found for the branch $CURRENT_BRANCH, falling back to main."
    BASE_BRANCH="main"
  fi
else
  echo "Detected the pull request's base branch: $BASE_BRANCH"
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
echo "Checking words on ${ORIGIN}/${BASE_BRANCH}..HEAD ..."
python3 scripts/knowledge/check_words.py --base "${ORIGIN}/${BASE_BRANCH}"
