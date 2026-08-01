#!/usr/bin/env bash
#
# Decide which release branches a pull request should be backported to, and
# emit one `backport` job matrix entry per target as the `result` output.
#
# Driven by the `backport` workflow through the environment, from either of its
# two triggers:
#
#   EVENT_NAME=pull_request_target   a merged PR; the rules below decide
#   EVENT_NAME=issue_comment         a `/backport <version> ...` comment, which
#                                    names the targets outright
#
# Run it by hand to reproduce a decision -- with GITHUB_OUTPUT unset the result
# goes to stdout:
#
#   EVENT_NAME=pull_request_target PR_NUMBER=13346 PR_BASE=main \
#   PR_TITLE='fix(BA-1234): ...' MERGE_COMMIT=<sha> \
#   .github/scripts/decide-backport-targets.sh
#
# `bash -e` matches how GitHub runs a `run:` block. `pipefail` is deliberately
# left off: the trailer lookup below is a pipeline whose `grep` is expected to
# find nothing on most pull requests. Bash 4 builtins are avoided so that the
# script stays runnable on a stock macOS bash.
set -e

event_name="${EVENT_NAME:-}"
pr_number="${PR_NUMBER:-}"
pr_title="${PR_TITLE:-}"
pr_body="${PR_BODY:-}"
pr_labels="${PR_LABELS:-}"
pr_base="${PR_BASE:-}"
merge_commit="${MERGE_COMMIT:-}"
comment_body="${COMMENT_BODY:-}"
author_association="${AUTHOR_ASSOCIATION:-}"
pr_author_login="${PR_AUTHOR_LOGIN:-}"
registry="${REGISTRY:-.github/maintained-versions.yml}"
: "${GITHUB_OUTPUT:=/dev/stdout}"

maintained=()   # versions the registry declares alive
requested=()    # versions named by a `/backport` comment
targets=()      # release branches to back port to

# Leave the reason on the pull request and stop -- for a human who asked.
reply_and_exit() {
  gh pr comment "$pr_number" -b "$1"
  exit 0
}

# Leave the reason on the pull request and fail -- for a request that cannot be
# carried out, so that it is not mistaken for "nothing needed backporting".
reply_and_fail() {
  gh pr comment "$pr_number" -b "$1"
  echo "::error::$1"
  exit 1
}

# Say why in the job log and stop -- for anything nobody asked for.
skip_and_exit() {
  echo "::notice::$1"
  exit 0
}

# Write the step output and stop.
emit_and_exit() {
  echo "result=$1" >> "$GITHUB_OUTPUT"
  exit 0
}

is_maintained() {
  local version
  for version in "${maintained[@]}"; do
    [ "$version" = "$1" ] && return 0
  done
  return 1
}

# A `/backport` comment carries its own targets; a merged pull request does not.
if [ "$event_name" = "issue_comment" ]; then
  case "$author_association" in
    OWNER|MEMBER|COLLABORATOR)
      ;;
    *)
      # Replying here would let anyone make the bot comment at will.
      skip_and_exit "Ignoring '/backport' on #$pr_number from $author_association: owners, members and collaborators only."
      ;;
  esac

  pr=$(gh pr view "$pr_number" --json mergedAt,mergeCommit,baseRefName,labels,author)
  merge_commit=$(jq -r '.mergeCommit.oid // ""' <<< "$pr")
  pr_base=$(jq -r '.baseRefName' <<< "$pr")
  pr_labels=$(jq -r '[.labels[].name] | join(",")' <<< "$pr")
  pr_author_login=$(jq -r '.author.login' <<< "$pr")
  if [ -z "$(jq -r '.mergedAt // ""' <<< "$pr")" ] || [ -z "$merge_commit" ]; then
    reply_and_exit "\`/backport\` works on merged pull requests only."
  fi

  command_line=$(head -n 1 <<< "${comment_body//$'\r'/}")
  read -ra requested <<< "$(sed -E 's|^[[:space:]]*/backport[[:space:]]*||; s|,| |g' <<< "$command_line")"
  if [ ${#requested[@]} -eq 0 ]; then
    reply_and_exit "\`/backport\` requires one or more target versions, e.g. \`/backport 26.4\`."
  fi
fi

# A pull request against a release branch is itself a backport.
if [ "$pr_base" != "main" ]; then
  skip_and_exit "#$pr_number targets '$pr_base' rather than 'main'; nothing to backport."
fi
if [ -z "$merge_commit" ]; then
  skip_and_exit "#$pr_number has no merge commit; nothing to backport."
fi

# Assign before the loop: a `yq` failure inside `< <(...)` would go unnoticed and
# read as "no maintained versions", the silent skip this workflow exists to remove.
if ! registry_versions=$(yq -e '.versions[].version' "$registry" 2>&1); then
  echo "::error::'$registry' must hold a non-empty 'versions' list -- $registry_versions"
  exit 1
fi
while IFS= read -r version; do
  maintained+=("$version")
done <<< "$registry_versions"
echo "Maintained versions: ${maintained[*]}"

if [ ${#requested[@]} -gt 0 ]; then
  # `/backport` names the targets outright; the rules below do not apply.
  unknown=()
  for version in "${requested[@]}"; do
    if is_maintained "$version"; then
      targets+=("$version")
    else
      unknown+=("$version")
    fi
  done
  if [ ${#targets[@]} -eq 0 ]; then
    reply_and_exit "No maintained version matches \`${unknown[*]}\`. The maintained versions are \`${maintained[*]}\` (see \`$registry\`)."
  fi
  if [ ${#unknown[@]} -gt 0 ]; then
    echo "::warning::Ignoring '${unknown[*]}' requested on #$pr_number: not listed in $registry"
  fi
else
  # A `Backport:` trailer names the targets outright, whatever the prefix would
  # have chosen: it is how a `fix:` reaches only some of the versions, or none.
  trailer=$(grep -iE '^[[:space:]]*Backport:' <<< "${pr_body//$'\r'/}" | head -n 1 | sed -E 's/^[^:]*:[[:space:]]*//; s/,/ /g')
  read -ra trailer_versions <<< "$trailer"

  if [ ${#trailer_versions[@]} -eq 0 ]; then
    # No trailer: a `fix:` pull request targets every maintained version.
    if grep -qE '^fix(\([^)]*\))?!?:' <<< "$pr_title"; then
      targets=("${maintained[@]}")
    fi
  elif [ ${#trailer_versions[@]} -eq 1 ] && [ "$(tr '[:upper:]' '[:lower:]' <<< "${trailer_versions[0]}")" = "none" ]; then
    echo "The Backport: trailer of #$pr_number opts out; no backport target."
  else
    unknown=()
    for version in "${trailer_versions[@]}"; do
      if is_maintained "$version"; then
        targets+=("$version")
      else
        unknown+=("$version")
      fi
    done
    # Dropping the unknown ones and backporting the rest would leave a half-done
    # job looking green. Stop, say so, and let `/backport` redo it.
    if [ ${#unknown[@]} -gt 0 ]; then
      reply_and_fail "The \`Backport:\` trailer names \`${unknown[*]}\`, which is not among the maintained versions \`${maintained[*]}\` (see \`$registry\`). Nothing was backported -- comment \`/backport <version>\` once the line is right."
    fi
  fi
fi

if [ ${#targets[@]} -gt 0 ]; then
  sorted=()
  while IFS= read -r version; do
    sorted+=("$version")
  done < <(printf '%s\n' "${targets[@]}" | sort -Vr -u)
  targets=("${sorted[@]}")
fi
echo "Backport targets of #$pr_number: ${targets[*]}"
if [ ${#targets[@]} -eq 0 ]; then
  emit_and_exit "[]"
fi

existing=()
for branch in "${targets[@]}"; do
  if git ls-remote --exit-code --heads origin "$branch" > /dev/null 2>&1; then
    existing+=("$branch")
  else
    echo "::warning::Skipping the '$branch' backport of #$pr_number: the release branch does not exist"
  fi
done
if [ ${#existing[@]} -eq 0 ]; then
  emit_and_exit "[]"
fi

git fetch --depth=1 origin "$merge_commit"
commit_headline=$(git show -s --format=%s "$merge_commit")
author=$(git show -s --format=%an "$merge_commit")
author_email=$(git show -s --format=%ae "$merge_commit")

# One entry per target branch, consumed as the `backport` job matrix.
emit_and_exit "$(jq -nc \
  --arg commit "$merge_commit" \
  --arg headline "$commit_headline" \
  --arg pr "$pr_number" \
  --arg author "$author" \
  --arg email "$author_email" \
  --arg login "$pr_author_login" \
  --arg labels "$pr_labels" \
  '$ARGS.positional | map({
    commit: $commit,
    target_branch: .,
    commit_headline: $headline,
    pr_number: $pr,
    author: $author,
    author_email: $email,
    author_login: $login,
    labels: $labels
  })' \
  --args "${existing[@]}")"
