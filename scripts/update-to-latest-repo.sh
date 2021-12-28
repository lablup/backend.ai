#!/bin/bash
INSTALL_PATH="{HOME}/backend.ai-dev"
cd ${INSTALL_PATH}
for d in agent backend.ai client-py common manager
do
    cd ${d}
    pip install --upgrade pip
    git fetch
    git pull
    pip install -U -r ./requirements/dev.txt
    pip install -e . -e ../common
    cd ..
done
cd manager
pip install ../common
