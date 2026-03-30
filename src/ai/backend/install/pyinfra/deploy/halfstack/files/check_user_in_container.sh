#!/bin/bash

which docker-compose || docker-compose() {
    docker compose "$@"
}
COMPSTR=".Service"
for nn in $(docker-compose ps --format json | jq "$COMPSTR" )
do
	sname=$(echo "$nn" | xargs)
	runuser=$(docker-compose ps "$sname" -q | \
	        xargs docker inspect --format '{{ .Config.User }}')
	echo 'The user of "'"$sname"'" is "'"$runuser"'"'
done