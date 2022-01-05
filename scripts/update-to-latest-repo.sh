#!/bin/bash
INSTALL_PATH="./backend.ai-dev"
BRANCH_VERSION="main"
cd ${INSTALL_PATH}
for d in backend.ai 
do
  cd ${d}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  cd ..
done
for d in common
do
  cd ${d}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  pip install -U -r ./requirements/dev.txt
  cd ..
done
for d in agent storage-proxy client-py manager
do
  cd ${d}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  pip install -U -r ./requirements/dev.txt
  pip install -U -e ../common
  cd ..
done
cd webserver
pip install -U pip
pip install -U -e .
pip install -U -e ../client-py
cd ..
cd manager
alembic upgrade head
