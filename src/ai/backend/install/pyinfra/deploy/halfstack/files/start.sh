#!/bin/bash

shopt -s expand_aliases
alias docker-compose > /dev/null 2>&1 || \
docker compose version > /dev/null 2>&1 && alias docker-compose="docker compose"

set -e

pushd "$(dirname "$0")" > /dev/null
## When not using pyinfra you have to create data directory
## Please changed the path of data directory and uncomment
# source .env
# mkdir -p "${TARGET_HOME_DIR:?error}/.data/backend.ai/etcd-cluster/${ETCD_CLUSTER_NAME:?error}/${THIS_ETCD_NODE_NAME:?error}"
# chmod 700 "${TARGET_HOME_DIR:?error}/.data/backend.ai/etcd-cluster/${ETCD_CLUSTER_NAME:?error}/${THIS_ETCD_NODE_NAME:?error}"

docker-compose up -d
./apply_pids_limit_to_existing_docker.sh
popd > /dev/null
