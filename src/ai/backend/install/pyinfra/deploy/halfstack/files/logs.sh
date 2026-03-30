#!/bin/bash

shopt -s expand_aliases
alias docker-compose > /dev/null 2>&1 || \
docker compose version > /dev/null 2>&1  && alias docker-compose="docker compose"

pushd "$(dirname "$0")" > /dev/null || exit $?
docker-compose logs "$@" || exit $?
popd > /dev/null || exit $?
