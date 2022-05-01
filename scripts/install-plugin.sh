#! /bin/bash

mkdir -p ./plugins
PLUGIN_OWNER=$(echo $1 | cut -d / -f 1)
PLUGIN_REPO=$(echo $1 | cut -d / -f 2)
git clone "https://github.com/lablup/$1" "./plugins/$PLUGIN_REPO"
source "dist/export/python/virtualenvs/python-default/${PY:-$(python --version|awk '{ print $2 }')}/bin/activate"
pip install -e "./plugins/$PLUGIN_REPO"
