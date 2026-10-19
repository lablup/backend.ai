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
# Read the label from the archive instead of loading it, so the local daemon
# keeps the image of its own architecture under the same tag.
ARCHIVE="$OUT_DIR/backendai-socket-relay.img.x86_64.tar.gz"
CONFIG_BLOB=$(tar -xzOf "$ARCHIVE" manifest.json | jq -r '.[0].Config')
tar -xzOf "$ARCHIVE" "$CONFIG_BLOB" | jq -r '.config.Labels."ai.backend.version"' \
  > "$OUT_DIR/backendai-socket-relay.version.txt"
