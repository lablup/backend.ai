#!/usr/bin/env bash
#
# Decide whether a push saves the CI caches.
#
#   decide-cache-save.sh <repo> <branch> <sha>
#
#     <repo>    the repository to ask, e.g. lablup/backend.ai
#     <branch>  the branch the push landed on, e.g. main or 26.4
#     <sha>     the commit the push carries
#
# Prints `true` when <branch> is `main` or a version listed in `main`'s
# `.github/maintained-versions.yml`, and <sha> is still the tip of <branch>;
# `false` otherwise, with the reason on stderr.
#
# Pull requests read the caches of their base branch and then of `main`, so
# only those branches save. Pushes to them do not cancel one another, so a run
# for an older commit that finishes late must not save over the newer one.
# The registry is read from `main`, which a release branch's copy may lag.
#
# The arguments decide everything -- no CI environment is read and nothing has
# to be checked out. `gh` takes its credentials from GH_TOKEN under CI and from
# `gh auth login` elsewhere. Run it against the live repository:
#
#   .github/scripts/decide-cache-save.sh lablup/backend.ai main "$(git rev-parse origin/main)"
set -e

usage() {
  echo "Usage: $0 <repo> <branch> <sha>"
  echo "  <repo>    the repository to ask, e.g. lablup/backend.ai"
  echo "  <branch>  the branch the push landed on, e.g. main or 26.4"
  echo "  <sha>     the commit the push carries"
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

if [ "$branch" != main ]; then
  maintained=$(gh api -H "Accept: application/vnd.github.raw" \
    "repos/$repo/contents/.github/maintained-versions.yml?ref=main" \
    | yq -e '.versions[].version')
  if ! grep -qxF "$branch" <<< "$maintained"; then
    echo "$branch is neither main nor a maintained version." >&2
    echo false
    exit 0
  fi
fi

tip=$(gh api "repos/$repo/commits/$branch" --jq .sha)
if [ "$tip" != "$sha" ]; then
  echo "$sha is not the tip of $branch ($tip)." >&2
  echo false
  exit 0
fi
echo true
