#!/bin/bash
set -e

# Configuration for DGX Spark (ARM64) testing
IMAGE_NAME="${IMAGE_NAME:-backendai-agent}"
VERSION="${VERSION:-latest}"
PLATFORM="${PLATFORM:-linux/arm64}"

# Step 1: Build wheels using Pants
echo "Building wheels with Pants..."
./scripts/build-wheels.sh

# Step 2: Build Docker image with pre-built wheels
echo "Building Docker image..."
docker build \
  --platform "${PLATFORM}" \
  --file docker/agent/Dockerfile \
  --tag "${IMAGE_NAME}:${VERSION}" \
  .

echo "Built: ${IMAGE_NAME}:${VERSION}"

# Auto-load to k3s if detected
if command -v k3s &> /dev/null; then
  echo ""
  echo "k3s detected - loading image to k3s containerd..."
  docker save "${IMAGE_NAME}:${VERSION}" | sudo k3s ctr images import -
  echo "✓ Image loaded to k3s"
fi
