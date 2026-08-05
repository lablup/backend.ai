#!/usr/bin/env bash
#
# Decide which release branches a pull request should be backported to, and
# print one `backport` job matrix entry per target -- a single line of JSON,
# `[]` when nothing is to be backported.
#
#   decide-backport-targets.sh --event <name> --pr <number> [options]
#
#     --event <name>            pull_request_target, a merged pull request whose
#                               metadata the rules below decide from, or
#                               issue_comment, a `/backport <version> ...`
#                               comment naming the targets outright
#     --pr <number>             the pull request to back port
#     --title <t>               its title, which the `fix:` rule reads
#     --body <b>                its body, which carries the `Backport:` trailer
#     --labels <csv>            its labels, carried onto the backport
#     --base <ref>              the branch it was merged into
#     --merge-commit <sha>      the commit to cherry-pick
#     --comment-body <b>        the `/backport` comment, for --event issue_comment
#     --author-association <a>  who wrote that comment, e.g. MEMBER
#     --pr-author <login>       who the backport is assigned to
#     --registry <path>         the maintained-version registry
#                               (default: .github/maintained-versions.yml)
#     --dry-run                 decide as usual, but report the pull request
#                               comments instead of posting them
#
# The arguments decide everything -- no CI environment is read. Everything a
# human reads goes to stderr, so stdout holds the matrix and nothing else. Run
# it against your own checkout to reproduce a decision:
#
#   .github/scripts/decide-backport-targets.sh --event pull_request_target \
#     --pr 13346 --base main --title 'fix(BA-1234): ...' \
#     --merge-commit <sha> --dry-run
#
# `gh` takes its credentials from GH_TOKEN under CI and from `gh auth login`
# elsewhere. `bash -e` matches how GitHub runs a `run:` block. `pipefail` is
# deliberately left off: the trailer lookup below is a pipeline whose `grep` is
# expected to find nothing on most pull requests. Bash 4 builtins are avoided so
# that the script stays runnable on a stock macOS bash.
set -e

usage() {
  echo "Usage: $0 --event <name> --pr <number> [options]"
  echo "  --event <name>            pull_request_target or issue_comment"
  echo "  --pr <number>             the pull request to back port"
  echo "  --title <t>               its title"
  echo "  --body <b>                its body, carrying the 'Backport:' trailer"
  echo "  --labels <csv>            its labels"
  echo "  --base <ref>              the branch it was merged into"
  echo "  --merge-commit <sha>      the commit to cherry-pick"
  echo "  --comment-body <b>        the '/backport' comment"
  echo "  --author-association <a>  who wrote that comment"
  echo "  --pr-author <login>       who the backport is assigned to"
  echo "  --registry <path>         maintained-version registry"
  echo "                            (default: .github/maintained-versions.yml)"
  echo "  --dry-run                 report the pull request comments, post none"
}

event_name=""
pr_number=""
pr_title=""
pr_body=""
pr_labels=""
pr_base=""
merge_commit=""
comment_body=""
author_association=""
pr_author_login=""
registry=".github/maintained-versions.yml"
dry_run=0

while [ "$#" -gt 0 ]; do
  # Every option but `--dry-run` takes a value; catching a missing one here
  # keeps each branch below to a single assignment.
  case "$1" in
    --dry-run|-h|--help) ;;
    *) [ "$#" -ge 2 ] || { echo "Error: $1 requires a value" >&2; usage >&2; exit 2; } ;;
  esac
  case "$1" in
    --event) event_name="$2"; shift ;;
    --pr) pr_number="$2"; shift ;;
    --title) pr_title="$2"; shift ;;
    --body) pr_body="$2"; shift ;;
    --labels) pr_labels="$2"; shift ;;
    --base) pr_base="$2"; shift ;;
    --merge-commit) merge_commit="$2"; shift ;;
    --comment-body) comment_body="$2"; shift ;;
    --author-association) author_association="$2"; shift ;;
    --pr-author) pr_author_login="$2"; shift ;;
    --registry) registry="$2"; shift ;;
    --dry-run) dry_run=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$event_name" ] || [ -z "$pr_number" ]; then
  echo "Error: --event and --pr are required" >&2
  usage >&2
  exit 2
fi

maintained=()   # versions the registry declares alive
requested=()    # versions named by a `/backport` comment
targets=()      # release branches to back port to

# The one side effect this script has, and the only thing `--dry-run` withholds.
comment_on_pr() {
  if [ "$dry_run" -eq 1 ]; then
    echo "dry run, would comment on #$pr_number: $1" >&2
  else
    gh pr comment "$pr_number" -b "$1"
  fi
}

# Leave the reason on the pull request and stop -- for a human who asked.
reply_and_exit() {
  comment_on_pr "$1"
  exit 0
}

# Leave the reason on the pull request and fail -- for a request that cannot be
# carried out, so that it is not mistaken for "nothing needed backporting".
reply_and_fail() {
  comment_on_pr "$1"
  echo "$1" >&2
  exit 1
}

# Say why and stop -- for anything nobody asked for.
skip_and_exit() {
  echo "$1" >&2
  exit 0
}

# Print the matrix and stop.
emit_and_exit() {
  echo "$1"
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
  echo "'$registry' must hold a non-empty 'versions' list -- $registry_versions" >&2
  exit 1
fi
while IFS= read -r version; do
  maintained+=("$version")
done <<< "$registry_versions"
echo "Maintained versions: ${maintained[*]}" >&2

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
    echo "Ignoring '${unknown[*]}' requested on #$pr_number: not listed in $registry" >&2
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
    echo "The Backport: trailer of #$pr_number opts out; no backport target." >&2
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
echo "Backport targets of #$pr_number: ${targets[*]}" >&2
if [ ${#targets[@]} -eq 0 ]; then
  emit_and_exit "[]"
fi

existing=()
for branch in "${targets[@]}"; do
  if git ls-remote --exit-code --heads origin "$branch" > /dev/null 2>&1; then
    existing+=("$branch")
  else
    echo "Skipping the '$branch' backport of #$pr_number: the release branch does not exist" >&2
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
