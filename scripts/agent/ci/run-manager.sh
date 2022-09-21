#! /bin/bash
set -e
source ~/virtualenv/manager/bin/activate

set -v
cd ${HOME}/build/lablup/backend.ai-manager
python -c 'import sys; print(sys.prefix)'
python -m ai.backend.manager.cli schema oneshot head
python -m ai.backend.manager.cli fixture populate example_keypair
python -m ai.backend.manager.cli etcd put volumes/_mount /tmp/vfolders
python -m ai.backend.gateway.server \
  --etcd-addr ${BACKEND_ETCD_ADDR} \
  --namespace ${BACKEND_NAMESPACE} \
  --redis-addr ${BACKEND_REDIS_ADDR} \
  --db-addr ${BACKEND_DB_ADDR} \
  --db-name ${BACKEND_DB_NAME} \
  --db-user ${BACKEND_DB_USER} \
  --db-password "${BACKEND_DB_PASSWORD}" \
  --service-ip 127.0.0.1 \
  --service-port 5001 \
  --events-port 5002 &
