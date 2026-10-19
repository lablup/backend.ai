#! /bin/bash
set -euo pipefail
IMG="backendai-socket-relay:latest"
OUT_DIR="src/ai/backend/agent/docker"
for ARCH in x86_64 aarch64; do
  case "$ARCH" in
    x86_64) PLATFORM="linux/amd64" ;;
    aarch64) PLATFORM="linux/arm64" ;;
  esac
  # The docker exporter writes an archive that `docker load` accepts on daemons
  # with either the classic or the containerd image store.
  docker buildx build --platform "$PLATFORM" --provenance=false --sbom=false \
    -f docker/socket-relay.dockerfile -t "$IMG" --output "type=docker,dest=-" docker \
    | gzip > "$OUT_DIR/backendai-socket-relay.img.$ARCH.tar.gz"
done
gzip -dc "$OUT_DIR/backendai-socket-relay.img.$ARCH.tar.gz" | docker load -q
docker image inspect "$IMG" | jq -r '.[0].Config.Labels."ai.backend.version"' > "$OUT_DIR/backendai-socket-relay.version.txt"
