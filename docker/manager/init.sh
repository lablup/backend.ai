#! /bin/sh
set -e

cd /app

wait-for backendai-etcd:2379
wait-for backendai-db:5432

if [ ! -f alembic.ini ]; then
  echo 'Initializing for the first time...'
  cp alembic.ini.sample alembic.ini
  sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql+asyncpg://postgres:develove@backendai-db:5432/backend!' alembic.ini
  python -m ai.backend.manager.cli schema oneshot head
  python -m ai.backend.manager.cli fixture populate example_keypair
  python -m ai.backend.manager.cli etcd update-images -f sample-configs/image-metadata.yml
  python -m ai.backend.manager.cli etcd update-aliases -f sample-configs/image-aliases.yml
  python -m ai.backend.manager.cli etcd put volumes/_mount /tmp/vfolders
fi

echo 'Launching the API gateway...'
exec python -m ai.backend.gateway.server
