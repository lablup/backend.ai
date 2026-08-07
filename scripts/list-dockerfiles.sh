#!/bin/bash
# List the dockerfiles under docker/ as a GitHub Actions build matrix.
#
# Usage:
#   scripts/list-dockerfiles.sh [--all|--service|--infra]
#
# Prints a compact {"include": [...]} JSON document to stdout.
#
# Service images (docker/backend.ai-*.dockerfile / .Dockerfile) are built from
# the repository root (they install the wheels staged in dist/) and map to a
# Docker Hub repository:
#   {"name": "backend.ai-manager", "dockerfile": "docker/backend.ai-manager.Dockerfile",
#    "context": ".", "image": "lablup/backend.ai-manager"}
#
# Infra images (every other dockerfile) are built from the docker/ directory
# and are not published:
#   {"name": "krunner-extractor", "dockerfile": "docker/krunner-extractor.dockerfile",
#    "context": "docker"}
set -euo pipefail

usage() {
  echo "usage: $0 [--all|--service|--infra]" >&2
  exit 2
}

mode="all"
case "${1:---all}" in
  --all) mode="all" ;;
  --service) mode="service" ;;
  --infra) mode="infra" ;;
  *) usage ;;
esac
[ "$#" -le 1 ] || usage

cd "$(dirname "$0")/.."

find docker -type f \( -name '*.dockerfile' -o -name '*.Dockerfile' \) \
  | LC_ALL=C sort \
  | jq -R -s -c --arg mode "$mode" '
      split("\n")
      | map(select(length > 0))
      | map(
          (split("/")[-1] | sub("\\.[dD]ockerfile$"; "")) as $name
          | if ($name | startswith("backend.ai-")) then
              {category: "service", name: $name, dockerfile: .,
               context: ".", image: ("lablup/" + $name)}
            else
              {category: "infra", name: $name, dockerfile: ., context: "docker"}
            end
        )
      | map(select($mode == "all" or .category == $mode))
      | map(del(.category))
      | {include: .}
    '
