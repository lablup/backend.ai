#!/usr/bin/env bash
#
# Open a pull request with the files `go generate ./...` changed.
#
#   open-go-generate-pr.sh <commit> <base> [--dry-run]
#
#     <commit>    the revision the generation ran on, e.g. the push commit on `v2`
#     <base>      the branch the pull request targets
#     --dry-run   list the changed files; push nothing, open nothing
#
# Run it from the worktree after `go generate ./...`: the changed files are the
# input. The branch is built with plumbing on top of <commit>, so neither HEAD nor
# the worktree moves. It exits 0 with the reason when nothing changed.
#
# `gh` takes its credentials from GH_TOKEN under CI and from `gh auth login`
# elsewhere. `bash -e` matches how GitHub runs a `run:` block.
set -e

usage() {
  echo "Usage: $0 <commit> <base> [--dry-run]"
  echo "  <commit>    the revision the generation ran on"
  echo "  <base>      the branch the pull request targets"
  echo "  --dry-run   list the changed files; push nothing, open nothing"
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
if [ "${#positional[@]}" -ne 2 ]; then
  echo "Error: <commit> and <base> are required" >&2
  usage >&2
  exit 2
fi
commit=$(git rev-parse --verify "${positional[0]}^{commit}")
base="${positional[1]}"
branch="go-generate/$base"
title="chore: regenerate Go code"

cd "$(git rev-parse --show-toplevel)"

# Stage the worktree in a scratch index on top of <commit>.
index=$(mktemp -u)
trap 'rm -f "$index"' EXIT
export GIT_INDEX_FILE="$index"
git read-tree "$commit"
git add -A
changed=$(git diff --cached --name-only "$commit")
if [ -z "$changed" ]; then
  echo "The generated code at $commit is up to date; nothing to open."
  exit 0
fi
if [ "$dry_run" = 1 ]; then
  echo "Would open '$title' from '$branch' changing:"
  echo "$changed"
  exit 0
fi
tree=$(git write-tree)
new=$(
  GIT_AUTHOR_NAME='github-actions[bot]' \
  GIT_AUTHOR_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  GIT_COMMITTER_NAME='github-actions[bot]' \
  GIT_COMMITTER_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  git commit-tree "$tree" -p "$commit" -m "$title"
)
unset GIT_INDEX_FILE

# One branch, force-pushed: a later push revises the open pull request instead of
# opening a second one.
git push --force origin "$new:refs/heads/$branch"

existing=$(gh pr list --head "$branch" --base "$base" --state open --json number --jq '.[0].number // ""')
if [ -n "$existing" ]; then
  echo "Revised the open pull request #$existing."
  exit 0
fi
body="\`go generate ./...\` on \`$base\` at $commit changes the files below. This commits the regenerated output.

$(echo "$changed" | sed 's/^/- `/; s/$/`/')"
gh pr create --base "$base" --head "$branch" --title "$title" --body "$body" --label skip:changelog
