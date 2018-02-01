#! /bin/sh
cd /app

echo 'starting...'

if [ ! -f alembic.ini ]; then
  echo 'initializing...'
  cp alembic.ini.sample alembic.ini
  sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql://postgres:develove@backendai-db:5432/backend!' alembic.ini
  python -m ai.backend.manager.cli schema oneshot head
  python -m ai.backend.manager.cli fixture populate example_keypair
  python -m ai.backend.manager.cli update-images -f sample-configs/image-metadata.yml
  python -m ai.backend.manager.cli update-aliases -f sample-configs/image-aliases.yml
  python -m ai.backend.manager.cli etcd put volumes/_mount /tmp
  python -m ai.backend.manager.cli etcd put volumes/_vfroot vfroot
fi

echo 'launching manager...'
exec python -m ai.backend.gateway.server

#ETCDCTL_API=3 etcdctl --endpoints http://backendai-etcd:2379 \
#              put /sorna/local/volumes/_vfroot /tmp/vfroot
