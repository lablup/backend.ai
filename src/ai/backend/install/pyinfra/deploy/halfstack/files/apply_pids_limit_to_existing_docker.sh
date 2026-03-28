#!/bin/bash

set -e

pushd "$(dirname "$0")" > /dev/null
source .env

echo "PIDS_LIMIT_VALUE=${PIDS_LIMIT_VALUE:?error}"

for did in $(docker compose ps -q -a)
do
    APPLIED_VALUE="$( docker inspect --format '{{ .HostConfig.PidsLimit }}' "$did" )"
    [[ $APPLIED_VALUE == '<nil>' ]] && \
        docker container update --pids-limit="$PIDS_LIMIT_VALUE" "$did" || \
            echo "Not NIL"
    [[ $APPLIED_VALUE != "$PIDS_LIMIT_VALUE" ]] && \
        docker container update --pids-limit="$PIDS_LIMIT_VALUE" "$did" || \
            echo "The value alread applied"
    echo The value is "$( docker inspect --format '{{ .HostConfig.PidsLimit }}' "$did" )"
done

popd > /dev/null
