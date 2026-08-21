#!/bin/bash
# List the dockerfiles under docker/ as a GitHub Actions build matrix.
#
# Usage:
#   scripts/list-dockerfiles.sh [--all|--service|--infra]
#   scripts/list-dockerfiles.sh --help
#
# Prints a compact {"include": [...]} JSON document to stdout. The entries are
# the same set the workflows' previous inline `find` pipelines produced, in a
# deterministic order (LC_ALL=C sort by path) — set-identical, not
# byte-identical.
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
#
# Base images (BASE_IMAGES below) are backend.ai-* dockerfiles that service
# images build FROM: built inside the docker-images.yml bake run, never
# published, and emitted only with --all (no `image` field):
#   {"name": "backend.ai-base", "dockerfile": "docker/backend.ai-base.dockerfile",
#    "context": "."}
#
# Publishing is allowlist-driven: every backend.ai-* dockerfile must be
# registered in PUBLISHABLE_SERVICES (or BASE_IMAGES) below. An unregistered
# backend.ai-* dockerfile makes the script fail loudly, so a new dockerfile
# cannot start publishing an image without a deliberate registration edit here.
set -euo pipefail

# Registry of publishable service images (lowercase names):
# docker/<name>.dockerfile -> Docker Hub lablup/<name>.
PUBLISHABLE_SERVICES=(
  backend.ai-manager
  backend.ai-agent
  backend.ai-webserver
  backend.ai-storage-proxy
  backend.ai-client
  backend.ai-appproxy-coordinator
  backend.ai-appproxy-worker
)

# Registry of unpublished base images the service images build FROM
# (lowercase names). Built as bake dependencies of the service targets in
# docker-bake.hcl — not pushed anywhere, and not part of --service/--infra.
BASE_IMAGES=(
  backend.ai-base
)

print_usage() {
  echo "usage: $0 [--all|--service|--infra]"
  echo ""
  echo "Prints the docker/ dockerfile build matrix as compact JSON."
  echo "  --all       every dockerfile: service, infra, and base (default)"
  echo "  --service   publishable backend.ai-* images only"
  echo "  --infra     unpublished infra images only"
  echo "  --help, -h  show this help"
}

usage_error() {
  print_usage >&2
  exit 2
}

mode="all"
case "${1---all}" in
  --all) mode="all" ;;
  --service) mode="service" ;;
  --infra) mode="infra" ;;
  --help | -h)
    print_usage
    exit 0
    ;;
  *) usage_error ;;
esac
[ "$#" -le 1 ] || usage_error

unset CDPATH
cd -- "$(dirname "$0")/.." >/dev/null

[ -d docker ] || {
  echo "$0: docker/ directory not found under the repository root" >&2
  exit 1
}

files=$(find docker -type f \( -name '*.dockerfile' -o -name '*.Dockerfile' \) | LC_ALL=C sort)

# Fail loudly on any backend.ai-* dockerfile that is not a registered
# publishable service or base image, before emitting any JSON.
while IFS= read -r file; do
  [ -n "$file" ] || continue
  name="${file##*/}"
  name="${name%.dockerfile}"
  name="${name%.Dockerfile}"
  lower=$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    backend.ai-*)
      registered=false
      for svc in "${PUBLISHABLE_SERVICES[@]}" "${BASE_IMAGES[@]}"; do
        if [ "$lower" = "$svc" ]; then
          registered=true
          break
        fi
      done
      if [ "$registered" != true ]; then
        echo "$0: '$file' looks like a publishable service image, but '$name' is not registered in PUBLISHABLE_SERVICES (or BASE_IMAGES)." >&2
        echo "$0: register the name in scripts/list-dockerfiles.sh (or rename the dockerfile) to proceed." >&2
        exit 1
      fi
      ;;
  esac
done <<<"$files"

printf '%s\n' "$files" \
  | jq -R -s -c --arg mode "$mode" --arg base "${BASE_IMAGES[*]}" '
      ($base | split(" ")) as $base_names
      | split("\n")
      | map(select(length > 0))
      | map(
          (split("/")[-1] | sub("\\.[dD]ockerfile$"; "")) as $name
          | if ($base_names | index($name | ascii_downcase)) then
              {category: "base", name: $name, dockerfile: ., context: "."}
            elif ($name | ascii_downcase | startswith("backend.ai-")) then
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
