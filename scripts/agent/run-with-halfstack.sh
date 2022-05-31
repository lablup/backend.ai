#! /bin/sh

export BACKEND_ETCD_ADDR=localhost:8120

exec "$@"
