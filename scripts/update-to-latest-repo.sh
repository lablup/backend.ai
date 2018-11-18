#!/bin/bash
INSTALL_PATH="./backend.ai-dev"
cd ${INSTALL_PATH}
for d in agent backend.ai client-py common manager
do
  cd ${d}
  git fetch
  git pull
  cd ..
done
