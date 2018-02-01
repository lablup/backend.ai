#! /bin/sh
cd /app

echo 'Waiting for database...'
case $BACKEND_DB_ADDR in
  (*:*) DB_HOST=${BACKEND_DB_ADDR%:*} DB_PORT=${BACKEND_DB_ADDR##*:};;
  (*)   DB_HOST=$BACKEND_DB_ADDR      DB_PORT=5432;;
esac
export PGPASSWORD="$BACKEND_DB_PASSWORD"
until psql -h "$DB_HOST" -U "$BACKEND_DB_USER" -p $DB_PORT -c '\q'; do
  >&2 echo "(waiting...)"
  sleep 1
done
unset PGPASSWORD

if [ ! -f alembic.ini ]; then
  echo 'Initializing for the first time...'
  cp alembic.ini.sample alembic.ini
  sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql://postgres:develove@backendai-db:5432/backend!' alembic.ini
  python -m ai.backend.manager.cli schema oneshot head
  python -m ai.backend.manager.cli fixture populate example_keypair
  python -m ai.backend.manager.cli etcd update-images -f sample-configs/image-metadata.yml
  python -m ai.backend.manager.cli etcd update-aliases -f sample-configs/image-aliases.yml
  python -m ai.backend.manager.cli etcd put volumes/_mount /tmp
  python -m ai.backend.manager.cli etcd put volumes/_vfroot vfroot
fi

echo 'Launching the API gateway...'
exec python -m ai.backend.gateway.server
