#!/usr/bin/env bash
#
# Open a pull request advancing `main`'s NEXT_RELEASE_VERSION past the release
# line an `X.Y.0rc1` release commit cut.
#
#   bump-next-release-on-main.sh <commit> [--next <version>] [--dry-run]
#
#     <commit>          the release commit, e.g. the merge commit on `main`
#     --next <version>  the version to advance to (default: X.(Y+1).0), e.g.
#                       27.1.0 for a year rollover
#     --dry-run         report the decision; push nothing, open nothing
#
# Once `X.Y` is cut, every release of that line comes from its version branch,
# and `main` develops the next one. The commit subject names the release, and
# the branch is built with plumbing, so neither HEAD nor the worktree is touched.
#
# It exits 0 with the reason when the commit cuts no release line, or when
# `main` is already at the target or past it. It fails when `--next` is not past
# the line being cut.
#
# `gh` takes its credentials from GH_TOKEN under CI and from `gh auth login`
# elsewhere. `bash -e` matches how GitHub runs a `run:` block.
set -e

usage() {
  echo "Usage: $0 <commit> [--next <version>] [--dry-run]"
  echo "  <commit>          the release commit, e.g. the merge commit on \`main\`"
  echo "  --next <version>  the version to advance to (default: X.(Y+1).0)"
  echo "  --dry-run         report the decision; push nothing, open nothing"
}

dry_run=0
next=""
positional=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run=1 ;;
    --next)
      if [ "$#" -lt 2 ]; then
        echo "Error: --next requires a version" >&2
        usage >&2
        exit 2
      fi
      next="$2"
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) positional+=("$1") ;;
  esac
  shift
done
if [ "${#positional[@]}" -ne 1 ]; then
  echo "Error: exactly one commit is required" >&2
  usage >&2
  exit 2
fi
commit=$(git rev-parse "${positional[0]}")
subject=$(git log -1 --format=%s "$commit")

cd "$(git rev-parse --show-toplevel)"
meta=src/ai/backend/common/meta/meta.py
bump_script="$PWD/scripts/bump_next_release_version.py"

# The same rule `create-version-branch.sh` cuts a line by.
if [[ ! "$subject" =~ ^release:\ ([0-9]+)\.([0-9]+)\.0rc1( \(#[0-9]+\))?$ ]]; then
  echo "'$subject' cuts no release line; nothing to advance."
  exit 0
fi
line="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.0"
if [ -n "$next" ] && [[ ! "$next" =~ ^[0-9]+\.[0-9]+\.0$ ]]; then
  echo "Error: --next '$next' is not a sprint version (X.Y.0)." >&2
  exit 2
fi
target="${next:-${BASH_REMATCH[1]}.$((BASH_REMATCH[2] + 1)).0}"

# Sorts the versions given, oldest first.
version_sort() {
  printf '%s\n' "$@" | sort -V
}

if [ "$(version_sort "$target" "$line" | tail -n 1)" = "$line" ]; then
  echo "Error: '$target' is not past the line being cut ($line)." >&2
  exit 1
fi

# Keep a shallow clone shallow, and never shallow a full one.
depth=()
[ -e "$(git rev-parse --git-dir)/shallow" ] && depth=(--depth=1)
git fetch "${depth[@]}" origin main
base=$(git rev-parse FETCH_HEAD)

# Ask the script that owns the rewrite, run against a copy of main's file.
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/$(dirname "$meta")"
git show "$base:$meta" > "$scratch/$meta"
current=$(cd "$scratch" && python3 "$bump_script" --current)

if [ "$(version_sort "$current" "$target" | tail -n 1)" = "$current" ]; then
  echo "main is at NEXT_RELEASE_VERSION $current, already at or past $target."
  exit 0
fi

branch="next-release-version/$target"
# The `release:` prefix keeps this out of the news-fragment check, and the
# `Backport:` trailer keeps the version off the release branches.
title="release: bump NEXT_RELEASE_VERSION to $target"
body="\`$line\` is cut onto its version branch, so \`main\` now develops \`$target\`. This moves \`NEXT_RELEASE_VERSION\` from \`$current\` to \`$target\`.

Backport: none"

if [ "$dry_run" = 1 ]; then
  echo "Would open '$title' from '$branch' ($current -> $target)."
  exit 0
fi

(cd "$scratch" && python3 "$bump_script" "$target" > /dev/null)

index=$(mktemp -u)
tree=$(
  export GIT_INDEX_FILE="$index"
  git read-tree "$base"
  git update-index --add --cacheinfo "100644,$(git hash-object -w "$scratch/$meta"),$meta"
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

# One branch per target, force-pushed: a re-run revises its pull request instead
# of opening a second one.
git push --force origin "$new:refs/heads/$branch"

existing=$(gh pr list --head "$branch" --base main --state open --json number --jq '.[0].number // ""')
if [ -n "$existing" ]; then
  echo "Revised the open pull request #$existing."
  exit 0
fi
gh pr create --base main --head "$branch" --title "$title" --body "$body"
