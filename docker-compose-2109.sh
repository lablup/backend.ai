#! /bin/sh
export DATADIR_PREFIX=dev2109
exec docker-compose -f docker-compose.halfstack-2109.yml -p dev2109 "$@"
