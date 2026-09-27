#!/usr/bin/env bash
#
# Print whether a commit is still the tip of a branch.
#
#   check-branch-tip.sh <repo> <branch> <sha>
#
#     <repo>    the repository to ask, e.g. lablup/backend.ai
#     <branch>  the branch whose tip to compare against, e.g. main
#     <sha>     the commit to check
#
# Prints `true` when <sha> is the current tip of <branch>, `false` otherwise.
# CI saves its caches only from the tip of `main`: pushes to `main` do not
# cancel one another, so a run for an older commit that finishes late must not
# overwrite the entry the newer commit saved.
#
# The arguments decide everything -- no CI environment is read and nothing has
# to be checked out. `gh` takes its credentials from GH_TOKEN under CI and from
# `gh auth login` elsewhere. Run it against the live repository:
#
#   .github/scripts/check-branch-tip.sh lablup/backend.ai main "$(git rev-parse origin/main)"
set -e

usage() {
  echo "Usage: $0 <repo> <branch> <sha>"
  echo "  <repo>    the repository to ask, e.g. lablup/backend.ai"
  echo "  <branch>  the branch whose tip to compare against, e.g. main"
  echo "  <sha>     the commit to check"
}

positional=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -*) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) positional+=("$1") ;;
  esac
  shift
done
if [ "${#positional[@]}" -ne 3 ]; then
  echo "Error: expected <repo> <branch> <sha>" >&2
  usage >&2
  exit 2
fi
repo="${positional[0]}"
branch="${positional[1]}"
sha="${positional[2]}"

tip=$(gh api "repos/$repo/commits/$branch" --jq .sha)
if [ "$tip" = "$sha" ]; then
  echo true
else
  echo "$sha is not the tip of $branch ($tip)." >&2
  echo false
fi
