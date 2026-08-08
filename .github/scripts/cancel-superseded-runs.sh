#!/usr/bin/env bash
#
# Cancel workflow runs that a newer push to the same branch has superseded.
#
#   cancel-superseded-runs.sh <repo> <workflow> <branch> <head-sha> [--dry-run]
#
#     <repo>      the repository whose runs to inspect, e.g. lablup/backend.ai
#     <workflow>  the workflow file whose runs to inspect, e.g. ci.yml
#     <branch>    the head branch the push landed on
#     <head-sha>  the commit that supersedes the others; its runs are never
#                 touched
#     --dry-run   report which runs would be cancelled; cancel nothing
#
# `cancel-in-progress` on the workflow's own concurrency group intermittently
# misses the older run when two pushes land close together; the newer run then
# sits pending, jobless, until the older one finishes. This cancels the
# superseded run explicitly.
#
# Two guards keep it from cancelling the wrong run:
#   - only runs from <repo> itself are touched, so a fork branch that happens
#     to share the name cannot be hit;
#   - only runs older than <head-sha>'s own run are touched, so a canceller
#     that executes late can never cancel a run newer than its event.
#
# The arguments decide everything -- no CI environment is read and nothing has
# to be checked out. `gh` takes its credentials from GH_TOKEN under CI and from
# `gh auth login` elsewhere. Run it against the live repository:
#
#   .github/scripts/cancel-superseded-runs.sh lablup/backend.ai ci.yml \
#     my-branch "$(git rev-parse HEAD)" --dry-run
set -e

usage() {
  echo "Usage: $0 <repo> <workflow> <branch> <head-sha> [--dry-run]"
  echo "  <repo>      the repository whose runs to inspect, e.g. lablup/backend.ai"
  echo "  <workflow>  the workflow file whose runs to inspect, e.g. ci.yml"
  echo "  <branch>    the head branch the push landed on"
  echo "  <head-sha>  the commit that supersedes the others"
  echo "  --dry-run   report which runs would be cancelled; cancel nothing"
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
  echo "Error: expected <repo> <workflow> <branch> <head-sha>" >&2
  usage >&2
  exit 2
fi
repo="${positional[0]}"
workflow="${positional[1]}"
branch="${positional[2]}"
head_sha="${positional[3]}"

runs=$(gh api "repos/$repo/actions/workflows/$workflow/runs?branch=$branch&per_page=100" \
  --jq '.workflow_runs')

# The newest run of <head-sha> anchors the comparison: anything older than it
# is superseded, anything newer belongs to an event this invocation has not
# seen and must be left alone.
anchor=$(jq -r --arg sha "$head_sha" \
  '[.[] | select(.head_sha == $sha) | .id] | max // ""' <<< "$runs")
if [ -z "$anchor" ]; then
  echo "No $workflow run for $head_sha on $branch yet; nothing to compare against."
  exit 0
fi

targets=$(jq -r --arg sha "$head_sha" --arg repo "$repo" --argjson anchor "$anchor" '
  .[]
  | select(.id < $anchor)
  | select(.head_sha != $sha)
  | select(.status == "queued" or .status == "in_progress"
           or .status == "pending" or .status == "waiting")
  | select(.head_repository.full_name == $repo)
  | "\(.id) \(.status) \(.head_sha)"' <<< "$runs")

if [ -z "$targets" ]; then
  echo "No superseded $workflow run on $branch."
  exit 0
fi

while read -r id status sha; do
  if [ "$dry_run" = 1 ]; then
    echo "Would cancel run $id ($status, $sha): superseded by $head_sha."
    continue
  fi
  # A run may finish between the listing and the cancel; that is not a failure.
  if gh api --silent -X POST "repos/$repo/actions/runs/$id/cancel"; then
    echo "Cancelled run $id ($status, $sha): superseded by $head_sha."
  else
    echo "Run $id ($status, $sha) refused the cancel; likely finished already."
  fi
done <<< "$targets"
