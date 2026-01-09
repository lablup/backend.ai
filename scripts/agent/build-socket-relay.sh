#! /bin/bash
IMG="backendai-socket-relay:latest"
docker build -f docker/socket-relay.dockerfile -t "$IMG" docker
docker image inspect "$IMG" | jq -r '.[0].ContainerConfig.Labels."ai.backend.version"' > src/ai/backend/agent/docker/backendai-socket-relay.version.txt
docker save "$IMG" | gzip > src/ai/backend/agent/docker/backendai-socket-relay.img.tar.gz
