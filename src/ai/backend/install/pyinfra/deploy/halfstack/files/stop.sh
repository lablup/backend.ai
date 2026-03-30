#!/bin/bash

shopt -s expand_aliases
alias docker-compose > /dev/null 2>&1 || \
docker compose version > /dev/null 2>&1 && alias docker-compose="docker compose"

set -e 

pushd "$(dirname "$0")" > /dev/null
docker-compose down
popd > /dev/null
