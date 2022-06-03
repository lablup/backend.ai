#! /bin/bash
set -ev

cd ${HOME}/build/lablup
git clone https://github.com/lablup/backend.ai-manager.git
cd backend.ai-manager
python -m venv --system-site-packages ~/virtualenv/manager
set +v
source ~/virtualenv/manager/bin/activate
set -v

pip install -U pip setuptools
sed -i'' -e "s/{BRANCH}/$BRANCH/g" requirements-ci.txt
pip install -U --upgrade-strategy=eager -r requirements-ci.txt
psql -c 'CREATE DATABASE testing;' -U postgres
cp alembic.ini.sample alembic.ini
sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql://postgres@localhost:5432/testing!' alembic.ini
