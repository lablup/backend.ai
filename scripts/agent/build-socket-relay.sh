#! /bin/bash
IMG="backendai-socket-relay:latest"
docker build -t "$IMG" docker/socket-relay
docker image inspect "$IMG" | jq -r '.[0].ContainerConfig.Labels."ai.backend.version"' > src/ai/backend/agent/docker/backendai-socket-relay.version.txt
docker save "$IMG" | gzip > src/ai/backend/agent/docker/backendai-socket-relay.img.tar.gz
