#!/usr/bin/env bash
#
# Open a pull request carrying the changelog file a final release wrote on its
# version branch back to `main`.
#
#   sync-changelog-to-main.sh <version> [<commit>] [--dry-run]
#
#     <version>   the release to carry over, e.g. 26.8.0
#     <commit>    the revision holding its changelog (default: <version>, the
#                 release tag)
#     --dry-run   report the decision; push nothing, open nothing
#
# The arguments and the repository decide everything -- no CI environment is
# read, no particular revision has to be checked out, and the branch is built
# with plumbing, so neither HEAD nor the worktree is touched. Run it against
# your own checkout:
#
#   git fetch --tags && .github/scripts/sync-changelog-to-main.sh 26.8.0 --dry-run
#
# It exits 0 with the reason when there is nothing to carry over: a pre-release,
# a release line older than the changelog split, or a file already on `main`.
#
# `gh` takes its credentials from GH_TOKEN under CI and from `gh auth login`
# elsewhere. `bash -e` matches how GitHub runs a `run:` block.
set -e

usage() {
  echo "Usage: $0 <version> [<commit>] [--dry-run]"
  echo "  <version>   the release to carry the changelog of, e.g. 26.8.0"
  echo "  <commit>    the revision holding it (default: <version>, the release tag)"
  echo "  --dry-run   report the decision; push nothing, open nothing"
}

dry_run=0
positional=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) positional+=("$1") ;;
  esac
  shift
done
if [ "${#positional[@]}" -lt 1 ]; then
  echo "Error: the release version is required" >&2
  usage >&2
  exit 2
fi
version="${positional[0]}"
commit="${positional[1]:-$version}"
branch="changelog-sync/$version"

cd "$(git rev-parse --show-toplevel)"

# Every pre-release of a series writes into the same file as its final release,
# so only the final one is worth carrying over. Asked of the script that already
# owns the rule.
if [ "$(python3 scripts/determine-release-type.py "$version")" = "true" ]; then
  echo "$version is a pre-release; its changelog reaches main with the final release."
  exit 0
fi

# Ask the mapping rule for the file name rather than assembling it here.
path=$(python3 scripts/changelog_files.py "$version")

if ! git cat-file -e "$commit:$path" 2> /dev/null; then
  # A release line cut before the changelog was split has no such file. Say so
  # and stop: a release must not fail over this.
  echo "'$path' is absent at $commit; nothing to carry over to main."
  exit 0
fi

# Keep a shallow clone shallow, and never shallow a full one.
depth=()
[ -e "$(git rev-parse --git-dir)/shallow" ] && depth=(--depth=1)
git fetch "${depth[@]}" origin main
base=$(git rev-parse FETCH_HEAD)

if git diff --quiet "$base" "$commit" -- "$path"; then
  echo "'$path' on main already matches $version."
  exit 0
fi

# The `release:` prefix keeps this out of the news-fragment check, and the
# `Backport:` trailer keeps the file from travelling back to the release
# branches it came from.
title="release: sync $path of $version to main"
body="The $version release wrote \`$path\` on its own release branch. This copies that one file to \`main\`; nothing else from the release commit comes along.

Backport: none"

if [ "$dry_run" = 1 ]; then
  echo "Would open '$title' from '$branch':"
  git diff --stat "$base" "$commit" -- "$path"
  exit 0
fi

# One file on top of main -- a copy, not a cherry-pick: the release commit also
# carries version bumps and generated artifacts that must not reach `main`.
# Assembled in a scratch index so that the caller's HEAD and worktree stay put.
index=$(mktemp -u)
tree=$(
  export GIT_INDEX_FILE="$index"
  git read-tree "$base"
  git update-index --add --cacheinfo "100644,$(git rev-parse "$commit:$path"),$path"
  git write-tree
)
rm -f "$index"
new=$(
  GIT_AUTHOR_NAME='github-actions[bot]' \
  GIT_AUTHOR_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  GIT_COMMITTER_NAME='github-actions[bot]' \
  GIT_COMMITTER_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  git commit-tree "$tree" -p "$base" -m "$title"
)

# One branch per release, force-pushed: a re-run of the same release revises its
# pull request instead of opening a second one.
git push --force origin "$new:refs/heads/$branch"

existing=$(gh pr list --head "$branch" --base main --state open --json number --jq '.[0].number // ""')
if [ -n "$existing" ]; then
  echo "Revised the open pull request #$existing."
  exit 0
fi
gh pr create --base main --head "$branch" --title "$title" --body "$body"
