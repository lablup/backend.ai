#!/usr/bin/env bash
#
# Report the alembic migrations a pull request rewrites, deletes or renames
# rather than adds. A migration another database has already applied cannot be
# changed in place -- the change never reaches that database.
#
#   check-migration-edits.sh --base-sha <sha> --head-sha <sha> [options]
#
#     --base-sha <sha>  the commit the pull request would be merged into
#     --head-sha <sha>  the commit it would be merged from
#     --base-ref <ref>  the branch it is opened against, which decides how far
#                       the release marker below is trusted (default: main)
#     --labels <csv>    its labels, carrying the override below
#     --label <name>    the label that lets a finding through
#                       (default: allow:migration-edit)
#
# One finding per line on stdout, tab separated, worst first:
#
#   <severity>	<verb>	<path>	<what the migration is>
#
# `released` names a migration that has been through a release cut, `unreleased`
# one merged during the current development cycle, and `allowed` either of the
# two on a pull request carrying the override label. Exit 1 when a finding
# stands, 0 when there is none or the label carries them all.
#
# A migration the pull request adds is never a finding: repointing your own
# unmerged migration's down_revision, and inserting a backport into the main
# chain before merge, both leave the file added rather than modified.
#
# Whether a migration has been released is read off its `# Part of:` comment,
# which `scripts/freeze_release_version.py` rewrites from NEXT_RELEASE_VERSION
# to the version being cut. A release branch takes no cut of its own, so on one
# the marker says nothing and every migration counts as released.
#
# Both commits must be in the checkout -- `fetch-depth: 0`. Run it against your
# own to reproduce a decision:
#
#   .github/scripts/check-migration-edits.sh \
#     --base-sha origin/main --head-sha HEAD

set -e

usage() {
  echo "Usage: $0 --base-sha <sha> --head-sha <sha> [options]"
  echo "  --base-sha <sha>  the commit the pull request would be merged into"
  echo "  --head-sha <sha>  the commit it would be merged from"
  echo "  --base-ref <ref>  the branch it is opened against"
  echo "                    (default: main)"
  echo "  --labels <csv>    its labels"
  echo "  --label <name>    the label that lets a finding through"
  echo "                    (default: allow:migration-edit)"
}

base_sha=""
head_sha=""
base_ref="main"
pr_labels=""
override_label="allow:migration-edit"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    *) [ "$#" -ge 2 ] || { echo "Error: $1 requires a value" >&2; usage >&2; exit 2; } ;;
  esac
  case "$1" in
    --base-sha) base_sha="$2"; shift ;;
    --head-sha) head_sha="$2"; shift ;;
    --base-ref) base_ref="$2"; shift ;;
    --labels) pr_labels="$2"; shift ;;
    --label) override_label="$2"; shift ;;
    *) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$base_sha" ] || [ -z "$head_sha" ]; then
  echo "Error: --base-sha and --head-sha are required" >&2
  usage >&2
  exit 2
fi
if [ -z "$override_label" ]; then
  echo "Error: --label must not be empty" >&2
  usage >&2
  exit 2
fi

# A release branch carries the version in its name and takes no release cut of
# its own, so the `# Part of:` marker on it is left unfrozen and says nothing.
trust_marker=false
case "$base_ref" in
  main) trust_marker=true ;;
esac

overridden=false
case ",${pr_labels}," in
  *",${override_label},"*) overridden=true ;;
esac

# What the pre-image says about the release it went out in: the frozen version,
# an empty string while the placeholder still stands, or the marker's absence
# for a migration older than the convention.
describe_migration() {
  marker=$(git show "$base_sha:$1" 2>/dev/null | grep -m1 '^# Part of:' || true)
  case "$marker" in
    "") echo "released before the # Part of: marker" ;;
    *NEXT_RELEASE_VERSION*) echo "" ;;
    *) echo "released in ${marker#\# Part of: }" ;;
  esac
}

released=""
unreleased=""

while IFS="$(printf '\t')" read -r status old new; do
  # A diff that found nothing still reaches the loop as one empty line.
  [ -n "$status" ] || continue
  case "${status%%[0-9]*}" in
    A) continue ;;
    M) verb="rewrites"; path="$old" ;;
    D) verb="deletes"; path="$old" ;;
    R) verb="renames"; path="$old" ;;
    *) verb="changes"; path="$old" ;;
  esac
  case "$path" in
    */__init__.py) continue ;;
  esac

  description=$(describe_migration "$path")
  if [ -n "$description" ] || [ "$trust_marker" = false ]; then
    [ -n "$description" ] || description="released on $base_ref"
    released="${released}released	${verb}	${path}	${description}
"
  else
    unreleased="${unreleased}unreleased	${verb}	${path}	merged in the current development cycle
"
  fi
  # `new` is the rename destination, reported through the pre-image path above.
  : "$new"
done <<EOF
$(git diff --name-status --find-renames "$base_sha...$head_sha" \
  -- ':(glob)src/ai/backend/**/alembic/versions/*.py')
EOF

findings="${released}${unreleased}"
if [ -z "$findings" ]; then
  echo "The pull request edits no existing migration." >&2
  exit 0
fi

if [ "$overridden" = true ]; then
  printf '%s' "$findings" | sed 's/^[a-z]*/allowed/'
  echo "The pull request carries '$override_label'; the findings above stand as a record." >&2
  exit 0
fi

printf '%s' "$findings"
echo "A migration already applied elsewhere cannot be changed in place -- add a new migration instead, or carry '$override_label' to record why this one has to change. See src/ai/backend/manager/models/alembic/AGENTS.md." >&2
exit 1
