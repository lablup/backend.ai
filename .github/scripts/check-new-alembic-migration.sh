#!/usr/bin/env bash
#
# Report the manager alembic migrations a pull request adds. `main` takes no new
# migration; schema changes go to the goose migrations on `v2`.
#
#   check-new-alembic-migration.sh --base-sha <sha> --head-sha <sha> [options]
#
#     --base-sha <sha>  the commit the pull request would be merged into
#     --head-sha <sha>  the commit it would be merged from
#     --labels <csv>    its labels, carrying the override below
#     --label <name>    the label that lets a finding through
#                       (default: allow:alembic-migration)
#
# One added path per line on stdout. Exit 1 when a migration is added and the
# label is absent; with the label the paths are not printed and the exit is 0.
# Only manager/models/alembic/versions/ counts.
#
# Reproduce a decision against your own checkout:
#
#   .github/scripts/check-new-alembic-migration.sh \
#     --base-sha origin/main --head-sha HEAD

set -e

usage() {
  echo "Usage: $0 --base-sha <sha> --head-sha <sha> [options]"
  echo "  --base-sha <sha>  the commit the pull request would be merged into"
  echo "  --head-sha <sha>  the commit it would be merged from"
  echo "  --labels <csv>    its labels"
  echo "  --label <name>    the label that lets a finding through"
  echo "                    (default: allow:alembic-migration)"
}

base_sha=""
head_sha=""
pr_labels=""
override_label="allow:alembic-migration"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    *) [ "$#" -ge 2 ] || { echo "Error: $1 requires a value" >&2; usage >&2; exit 2; } ;;
  esac
  case "$1" in
    --base-sha) base_sha="$2"; shift ;;
    --head-sha) head_sha="$2"; shift ;;
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

added=$(git diff --name-only --diff-filter=A "$base_sha...$head_sha" \
  -- 'src/ai/backend/manager/models/alembic/versions/*.py' | grep -v '/__init__\.py$' || true)

if [ -z "$added" ]; then
  echo "The pull request adds no manager alembic migration." >&2
  exit 0
fi

case ",${pr_labels}," in
  *",${override_label},"*)
    echo "The pull request carries '$override_label'; add the same change as a goose migration on v2." >&2
    exit 0 ;;
esac

printf '%s\n' "$added"
echo "main takes no new alembic migration: make the schema change a goose migration on v2, or carry '$override_label' for a bug fix that needs it. See src/ai/backend/manager/models/alembic/AGENTS.md." >&2
exit 1
