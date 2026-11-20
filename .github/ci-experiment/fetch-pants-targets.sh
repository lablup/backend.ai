#!/usr/bin/env bash
#
# Wait for the `ci.yml` run of a commit to upload `ci-targets`, then download it.
#
#   fetch-pants-targets.sh <repo> <head-sha> <out-dir> [timeout-seconds]
#
# Prints the run id. Fails when `plan-targets` does not succeed or the wait times out.
set -euo pipefail

repo=$1
sha=$2
out=$3
timeout=${4:-1800}
deadline=$(( $(date +%s) + timeout ))

run_id=""
while [ -z "$run_id" ]; do
  run_id=$(gh run list -R "$repo" --workflow ci.yml --commit "$sha" --json databaseId \
    -q '.[0].databaseId // empty')
  if [ -z "$run_id" ]; then
    [ "$(date +%s)" -lt "$deadline" ] || { echo "no ci.yml run for $sha" >&2; exit 1; }
    sleep 20
  fi
done

while true; do
  conclusion=$(gh run view -R "$repo" "$run_id" --json jobs \
    -q '.jobs[] | select(.name == "plan-targets") | .conclusion')
  case "$conclusion" in
    success) break ;;
    "") ;;
    *) echo "plan-targets ended with $conclusion" >&2; exit 1 ;;
  esac
  [ "$(date +%s)" -lt "$deadline" ] || { echo "plan-targets did not finish" >&2; exit 1; }
  sleep 20
done

gh run download -R "$repo" "$run_id" -n ci-targets -D "$out" >&2
echo "$run_id"
