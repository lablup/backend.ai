#!/usr/bin/env bash
#
# Delete the cache entries one save has superseded.
#
#   prune-ref-caches.sh <repo> <ref> <key-prefix> <kept-key> [--dry-run]
#
#     <repo>        the repository whose caches to prune, e.g. lablup/backend.ai
#     <ref>         the ref the entries were saved under, e.g. refs/heads/main
#     <key-prefix>  the prefix the superseded entries share with <kept-key>
#     <kept-key>    the entry just saved
#     --dry-run     list the entries that would be deleted; delete nothing
#
# A restore by prefix takes the newest entry, so the older ones under the same
# ref and prefix are never read again. Only entries created before <kept-key>
# are deleted: a newer one belongs to a later save and is left alone. When
# <kept-key> is not there -- another job's save of it lost the race, or has not
# finished -- nothing is deleted.
#
# The arguments decide everything -- no CI environment is read and nothing has
# to be checked out. `gh` takes its credentials from GH_TOKEN under CI and from
# `gh auth login` elsewhere. Run it against the live repository:
#
#   .github/scripts/prune-ref-caches.sh lablup/backend.ai refs/heads/main \
#     pants-mypy-Linux- pants-mypy-Linux-<sha> --dry-run
set -e

usage() {
  echo "Usage: $0 <repo> <ref> <key-prefix> <kept-key> [--dry-run]"
  echo "  <repo>        the repository whose caches to prune, e.g. lablup/backend.ai"
  echo "  <ref>         the ref the entries were saved under, e.g. refs/heads/main"
  echo "  <key-prefix>  the prefix the superseded entries share with <kept-key>"
  echo "  <kept-key>    the entry just saved"
  echo "  --dry-run     list the entries that would be deleted; delete nothing"
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
if [ "${#positional[@]}" -ne 4 ]; then
  echo "Error: expected <repo> <ref> <key-prefix> <kept-key>" >&2
  usage >&2
  exit 2
fi
repo="${positional[0]}"
ref="${positional[1]}"
prefix="${positional[2]}"
kept="${positional[3]}"
case "$kept" in
  "$prefix"*) ;;
  *) echo "Error: $kept does not start with $prefix" >&2; exit 2 ;;
esac

entries=$(gh cache list --repo "$repo" --ref "$ref" --key "$prefix" --limit 1000 \
  --json id,key,createdAt,sizeInBytes)
kept_at=$(jq -r --arg key "$kept" '[.[] | select(.key == $key) | .createdAt] | min // ""' <<< "$entries")
if [ -z "$kept_at" ]; then
  echo "$kept is not under $ref; nothing to prune."
  exit 0
fi
targets=$(jq -r --arg key "$kept" --arg at "$kept_at" \
  '.[] | select(.key != $key and .createdAt < $at) | "\(.id) \(.sizeInBytes) \(.key)"' <<< "$entries")
if [ -z "$targets" ]; then
  echo "Nothing older than $kept under $ref."
  exit 0
fi

while read -r id size key; do
  if [ "$dry_run" = 1 ]; then
    echo "Would delete $key ($size bytes): superseded by $kept."
    continue
  fi
  # Another job pruning the same prefix may have deleted it first.
  if gh cache delete "$id" --repo "$repo" > /dev/null; then
    echo "Deleted $key ($size bytes): superseded by $kept."
  else
    echo "Could not delete $key; likely gone already."
  fi
done <<< "$targets"
