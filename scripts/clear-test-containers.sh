#! /bin/bash

docker ps -a -q --filter 'name=^test-' | xargs -r docker rm -f -v
docker network ls --filter 'name=^testnet-' --format '{{.ID}}' | xargs -r docker network rm
rm -rf ~/.cache/bai/testing/*
