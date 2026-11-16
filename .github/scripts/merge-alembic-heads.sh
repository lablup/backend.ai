#!/usr/bin/env bash
#
# Open a pull request adding an empty merge migration when the manager's alembic
# graph at a commit has more than one head.
#
#   merge-alembic-heads.sh <commit> [--dry-run]
#
#     <commit>    the revision to check, e.g. the merge commit on `main`
#     --dry-run   report the decision and print the migration; push nothing,
#                 open nothing
#
# The heads are read from <commit> itself, not from the worktree, and the branch
# is built with plumbing, so neither HEAD nor the worktree is touched. Run it
# against your own checkout:
#
#   git fetch origin main && .github/scripts/merge-alembic-heads.sh FETCH_HEAD --dry-run
#
# It exits 0 with the reason when the graph has a single head. The pull request
# carries `skip:changelog`: a merge migration changes nothing a user sees.
#
# `gh` takes its credentials from GH_TOKEN under CI and from `gh auth login`
# elsewhere. `bash -e` matches how GitHub runs a `run:` block.
set -e

usage() {
  echo "Usage: $0 <commit> [--dry-run]"
  echo "  <commit>    the revision to check, e.g. the merge commit on \`main\`"
  echo "  --dry-run   report the decision and print the migration; push nothing, open nothing"
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
if [ "${#positional[@]}" -ne 1 ]; then
  echo "Error: exactly one commit is required" >&2
  usage >&2
  exit 2
fi
commit=$(git rev-parse --verify "${positional[0]}^{commit}")
versions_dir="src/ai/backend/manager/models/alembic/versions"
branch="alembic/merge-heads"

cd "$(git rev-parse --show-toplevel)"

# Ask the script that already owns the graph walk, over a copy of the commit's
# migrations rather than whatever the worktree holds.
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
git archive "$commit" "$versions_dir" | tar -x -C "$scratch"
if report=$(python3 scripts/check-multiple-alembic-heads.py "$scratch/$versions_dir"); then
  echo "$report"
  echo "The alembic graph at $commit has a single head; nothing to merge."
  exit 0
fi
read -r -a heads <<< "$(echo "$report" | sed -n 's/^Detected head revisions: //p' | tr -d ',')"
if [ "${#heads[@]}" -lt 2 ]; then
  echo "Error: could not read the heads from: $report" >&2
  exit 1
fi

# The same shape `alembic revision` gives an id: the last 12 hex digits of a uuid4.
revision=$(python3 -c 'import uuid; print(uuid.uuid4().hex[-12:])')
path="$versions_dir/${revision}_merge_heads.py"
down_revision=$(printf '"%s", ' "${heads[@]}")
down_revision="(${down_revision%, })"
title="chore: merge diverged alembic heads"

content="\"\"\"Merge heads ${heads[*]}

Revisions written against the same parent landed independently, leaving the
graph with more than one head. The merge carries no statements.

Revision ID: $revision
Revises: $(IFS=,; echo "${heads[*]}" | sed 's/,/, /g')
Create Date: $(date -u +%Y-%m-%d)

\"\"\"

from __future__ import annotations

revision = \"$revision\"  # Part of: NEXT_RELEASE_VERSION
down_revision = $down_revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
"

if [ "$dry_run" = 1 ]; then
  echo "Would open '$title' from '$branch' adding '$path':"
  echo "$content"
  exit 0
fi

# One file on top of <commit>, assembled in a scratch index so that the caller's
# HEAD and worktree stay put.
blob=$(printf '%s' "$content" | git hash-object -w --stdin)
index=$(mktemp -u)
tree=$(
  export GIT_INDEX_FILE="$index"
  git read-tree "$commit"
  git update-index --add --cacheinfo "100644,$blob,$path"
  git write-tree
)
rm -f "$index"
new=$(
  GIT_AUTHOR_NAME='github-actions[bot]' \
  GIT_AUTHOR_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  GIT_COMMITTER_NAME='github-actions[bot]' \
  GIT_COMMITTER_EMAIL='41898282+github-actions[bot]@users.noreply.github.com' \
  git commit-tree "$tree" -p "$commit" -m "$title"
)

# One branch, force-pushed: a later divergence revises the open pull request
# instead of opening a second one.
git push --force origin "$new:refs/heads/$branch"

existing=$(gh pr list --head "$branch" --base main --state open --json number --jq '.[0].number // ""')
if [ -n "$existing" ]; then
  echo "Revised the open pull request #$existing."
  exit 0
fi
body="\`main\` has more than one alembic head: ${heads[*]}. This adds the empty merge migration \`$path\` whose \`down_revision\` is the tuple of those heads."
gh pr create --base main --head "$branch" --title "$title" --body "$body" --label skip:changelog
