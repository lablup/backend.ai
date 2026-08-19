#!/usr/bin/env bash
#
# Tag the release an `X.Y.0rc1` release commit made, and cut the `X.Y` version
# branch at that same commit.
#
#   create-version-branch.sh <commit>
#
#     <commit>    the release commit, e.g. the merge commit on `main`
#
# The commit decides everything: the subject `release.sh` left on it says which
# release this is, so no CI environment is read and no particular revision has to
# be checked out. Only refs are pushed, so neither HEAD nor the worktree is
# touched, and the decision it acted on is printed.
#
# It exits 0 with the reason when the commit cuts no release line -- a later rc,
# a final release, a patch release, or any other commit. It fails when the tag or
# the branch is already there: a line is cut once, and neither ref is ever moved.
#
# `bash -e` matches how GitHub runs a `run:` block.
set -e

usage() {
  echo "Usage: $0 <commit>"
  echo "  <commit>    the release commit, e.g. the merge commit on \`main\`"
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  -*) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
esac
if [ "$#" -ne 1 ]; then
  echo "Error: exactly one commit is required" >&2
  usage >&2
  exit 2
fi
commit=$(git rev-parse "$1")
subject=$(git log -1 --format=%s "$commit")

# `release.sh` commits `release: <target_version>` and the squash merge appends
# ` (#N)`, so the subject already names the release -- nothing else has to
# classify it. Only an `X.Y.0rc1` cuts a line, the same rule
# `update-maintained-versions.sh` registers a line by; a later rc, a final
# release or a patch release cuts nothing.
if [[ ! "$subject" =~ ^release:\ (([0-9]+\.[0-9]+)\.0rc1)( \(#[0-9]+\))?$ ]]; then
  echo "'$subject' cuts no release line; nothing to create."
  exit 0
fi
tag="${BASH_REMATCH[1]}"
branch="${BASH_REMATCH[2]}"

for ref in "refs/tags/$tag" "refs/heads/$branch"; do
  if git ls-remote --exit-code origin "$ref" > /dev/null 2>&1; then
    echo "Error: '$ref' already exists; a release line is cut once and neither ref is moved." >&2
    exit 1
  fi
done

# One atomic push, without `--force` and with both refspecs naming the same
# commit: the tag and the branch are created together at this very commit, or
# neither of them is.
git push --atomic origin \
  "$commit:refs/tags/$tag" \
  "$commit:refs/heads/$branch"
echo "Created tag '$tag' and branch '$branch' at $commit."
