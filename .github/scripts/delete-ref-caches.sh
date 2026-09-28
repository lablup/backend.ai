#!/usr/bin/env bash
#
# Delete every Actions cache entry saved under one ref.
#
#   delete-ref-caches.sh <repo> <ref> [--dry-run]
#
#     <repo>      the repository whose caches to delete, e.g. lablup/backend.ai
#     <ref>       the ref the entries were saved under, e.g. refs/pull/123/merge
#     --dry-run   list the entries that would be deleted; delete nothing
#
# A pull request's entries are readable only by runs of that pull request, so
# once it is closed they only take up the repository's cache quota.
#
# The arguments decide everything -- no CI environment is read and nothing has
# to be checked out. `gh` takes its credentials from GH_TOKEN under CI and from
# `gh auth login` elsewhere. Run it against the live repository:
#
#   .github/scripts/delete-ref-caches.sh lablup/backend.ai refs/pull/123/merge --dry-run
set -e

usage() {
  echo "Usage: $0 <repo> <ref> [--dry-run]"
  echo "  <repo>      the repository whose caches to delete, e.g. lablup/backend.ai"
  echo "  <ref>       the ref the entries were saved under, e.g. refs/pull/123/merge"
  echo "  --dry-run   list the entries that would be deleted; delete nothing"
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
  echo "Error: expected <repo> <ref>" >&2
  usage >&2
  exit 2
fi
repo="${positional[0]}"
ref="${positional[1]}"

entries=$(gh cache list --repo "$repo" --ref "$ref" --limit 1000 \
  --json id,key,sizeInBytes --jq '.[] | "\(.id) \(.sizeInBytes) \(.key)"')
if [ -z "$entries" ]; then
  echo "No cache entry under $ref."
  exit 0
fi

while read -r id size key; do
  if [ "$dry_run" = 1 ]; then
    echo "Would delete $key ($size bytes)."
    continue
  fi
  # Another run may delete or evict the entry between the listing and here.
  if gh cache delete "$id" --repo "$repo" > /dev/null; then
    echo "Deleted $key ($size bytes)."
  else
    echo "Could not delete $key; likely gone already."
  fi
done <<< "$entries"
