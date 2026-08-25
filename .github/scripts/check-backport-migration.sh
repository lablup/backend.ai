#!/usr/bin/env bash
#
# Warn about a pull request that will be backported and also changes the
# database schema. Such a migration is cherry-picked onto a release branch
# while its `main` counterpart stays where it is, so both have to be
# idempotent -- a requirement easy to miss while writing the migration and
# expensive to notice after the backport has been opened.
#
#   check-backport-migration.sh --pr <number> [options]
#
#     --pr <number>     the pull request to check
#     --title <t>       its title, which the `fix:` rule reads
#     --body <b>        its body, which carries the `Backport:` trailer
#     --labels <csv>    its labels, searched for the one below
#     --base <ref>      the branch it is opened against
#     --label <name>    the label a schema change carries, the one
#                       `.github/labeler.yml` puts on an alembic revision
#                       (default: require:db-migration)
#     --registry <path> the maintained-version registry
#                       (default: .github/maintained-versions.yml)
#
# Prints one line and exits 1 when the pull request is both; prints nothing
# and exits 0 otherwise. Which release branches a pull request reaches is not
# decided here -- `decide-backport-targets.sh` owns that rule and this script
# asks it. Nothing is written and no comment is posted, so the decision can be
# reproduced against your own checkout:
#
#   .github/scripts/check-backport-migration.sh --pr 13615 --base main \
#     --title 'fix(BA-1234): ...' --labels 'require:db-migration'
set -e

usage() {
  echo "Usage: $0 --pr <number> [options]"
  echo "  --pr <number>     the pull request to check"
  echo "  --title <t>       its title"
  echo "  --body <b>        its body, carrying the 'Backport:' trailer"
  echo "  --labels <csv>    its labels"
  echo "  --base <ref>      the branch it is opened against"
  echo "  --label <name>    the label a schema change carries"
  echo "                    (default: require:db-migration)"
  echo "  --registry <path> maintained-version registry"
  echo "                    (default: .github/maintained-versions.yml)"
}

pr_number=""
pr_title=""
pr_body=""
pr_labels=""
pr_base=""
# The label `.github/labeler.yml` puts on a pull request that adds an alembic
# revision. Named here so that renaming it there is a one-line change.
migration_label="require:db-migration"
registry=".github/maintained-versions.yml"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) ;;
    *) [ "$#" -ge 2 ] || { echo "Error: $1 requires a value" >&2; usage >&2; exit 2; } ;;
  esac
  case "$1" in
    --pr) pr_number="$2"; shift ;;
    --title) pr_title="$2"; shift ;;
    --body) pr_body="$2"; shift ;;
    --labels) pr_labels="$2"; shift ;;
    --base) pr_base="$2"; shift ;;
    --label) migration_label="$2"; shift ;;
    --registry) registry="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$pr_number" ]; then
  echo "Error: --pr is required" >&2
  usage >&2
  exit 2
fi
if [ -z "$migration_label" ]; then
  echo "Error: --label must not be empty" >&2
  usage >&2
  exit 2
fi

# The cheaper half of the question first: no schema change, nothing to warn
# about, and the registry stays unread.
case ",${pr_labels}," in
  *",${migration_label},"*) ;;
  *)
    echo "#$pr_number carries no '$migration_label' label; no migration to backport." >&2
    exit 0
    ;;
esac

script_dir=$(cd "$(dirname "$0")" && pwd)
status=0
targets=$("$script_dir/decide-backport-targets.sh" \
  --event pull_request \
  --targets-only \
  --pr "$pr_number" \
  --title "$pr_title" \
  --body "$pr_body" \
  --labels "$pr_labels" \
  --base "$pr_base" \
  --registry "$registry") || status=$?

# An undecidable target list -- a `Backport:` trailer naming a version nobody
# maintains, say -- is worth the same look as a decided one, and silence here
# would read as "no backport".
if [ "$status" -ne 0 ]; then
  echo "#$pr_number carries '$migration_label' and its backport targets could not be decided; see the reason logged above."
  exit 1
fi

if [ -z "$targets" ]; then
  echo "#$pr_number changes the schema but reaches no release branch." >&2
  exit 0
fi

# One line, so that the caller can hand it to whatever its CI annotates with.
echo "#$pr_number carries '$migration_label' and will be backported to ${targets// /, }. A migration that lands on both main and a release branch must be idempotent on each -- see src/ai/backend/manager/models/alembic/README.md."
exit 1
