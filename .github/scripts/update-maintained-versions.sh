#!/usr/bin/env bash
#
# Keep `.github/maintained-versions.yml` in step with the release lines.
#
#   update-maintained-versions.sh                     retire what is due
#   update-maintained-versions.sh <release> [--lts]   register a line if <release> cuts
#                                                     one, then retire what is due
#
# <release> is a full release version, the same string `scripts/release.sh` takes.
# `X.Y.0rc1` is the rc that cuts the `X.Y` branch and is the only form that
# registers a line; every other release -- a later rc, the GA, a patch -- leaves
# the registry alone. Nobody has to classify the release by hand.
#
# An LTS line is supported for a year, so registering one records a
# `retire_after` of the end of the same month one year on. If the rc period ran
# long enough to matter, edit the date by hand -- it is written down rather than
# recomputed so that it stays a decision, not a side effect of when a script ran.
#
# A regular line exists to get new features out quickly and is dropped as soon as
# any newer line is registered, LTS or not, so it carries no date. Should regular
# lines ever need backports of their own, this is the rule to revisit.
#
# The file is rewritten in place. `TODAY=YYYY-MM-DD` overrides the current date.
set -e

registry="${REGISTRY:-.github/maintained-versions.yml}"
today="${TODAY:-$(date -u +%F)}"
release=""
lts=false

while [ $# -gt 0 ]; do
  case "$1" in
    --lts) lts=true ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *)
      [ -z "$release" ] || { echo "Only one release may be given at a time." >&2; exit 2; }
      release="$1"
      ;;
  esac
  shift
done

if [ ! -f "$registry" ]; then
  echo "No registry at '$registry'." >&2
  exit 1
fi

days_in_month() {
  case "$2" in
    01|03|05|07|08|10|12) echo 31 ;;
    04|06|09|11) echo 30 ;;
    02)
      if [ $(( $1 % 4 )) -eq 0 ] && { [ $(( $1 % 100 )) -ne 0 ] || [ $(( $1 % 400 )) -eq 0 ]; }; then
        echo 29
      else
        echo 28
      fi
      ;;
    *) echo "Not a month: $2" >&2; exit 1 ;;
  esac
}

# End of the same month, one year on. ISO dates compare correctly as strings, so
# no date arithmetic beyond this is needed anywhere in this script.
end_of_month_next_year() {
  local year="${1%%-*}" month="${1:5:2}"
  year=$(( 10#$year + 1 ))
  printf '%04d-%s-%02d\n' "$year" "$month" "$(days_in_month "$year" "$month")"
}

drop() {
  version="$1" yq -i 'del(.versions[] | select(.version == strenv(version)))' "$registry"
  echo "  - $1 retired: $2"
}

version=""
if [ -n "$release" ]; then
  if [[ "$release" =~ ^([0-9]+\.[0-9]+)\.0rc1$ ]]; then
    version="${BASH_REMATCH[1]}"
  else
    echo "  . $release does not cut a release branch; leaving the registered lines alone"
  fi
fi

if [ -n "$version" ]; then
  if version="$version" yq -e '.versions[] | select(.version == strenv(version))' "$registry" > /dev/null 2>&1; then
    # Re-running the cut must not break the release; say so and carry on.
    echo "  . $version is already registered"
    version=""
  fi
fi

if [ -n "$version" ]; then
  if [ "$lts" = true ]; then
    retire_after=$(end_of_month_next_year "$today")
    version="$version" retire_after="$retire_after" yq -i \
      '.versions = [{"version": strenv(version), "lts": true, "retire_after": strenv(retire_after)}] + .versions' \
      "$registry"
    echo "  + $version registered as LTS, supported through $retire_after"
  else
    version="$version" yq -i '.versions = [{"version": strenv(version)}] + .versions' "$registry"
    echo "  + $version registered"
  fi
fi

entries=$(yq -o=json '.versions' "$registry")

# An LTS line goes when its recorded date has passed.
while IFS= read -r due; do
  [ -n "$due" ] || continue
  drop "$due" "supported through $(jq -r --arg v "$due" '.[] | select(.version == $v) | .retire_after' <<< "$entries")"
done < <(jq -r --arg today "$today" \
  '.[] | select(.lts == true) | select((.retire_after // "9999-12-31") < $today) | .version' <<< "$entries")

# A regular line stays only while it is the newest line there is.
newest=$(jq -r '.[].version' <<< "$entries" | sort -V | tail -n 1)
if [ -n "$newest" ]; then
  while IFS= read -r superseded; do
    [ -n "$superseded" ] || continue
    drop "$superseded" "superseded by $newest"
  done < <(jq -r --arg keep "$newest" \
    '.[] | select(.lts != true) | select(.version != $keep) | .version' <<< "$entries")
fi

echo "Maintained versions: $(yq -e '.versions[].version' "$registry" | tr '\n' ' ')"
