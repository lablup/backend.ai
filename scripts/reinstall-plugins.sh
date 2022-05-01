#! /bin/bash

PY=${PY:-$(python --version|awk '{ print $2 }')}
source "dist/export/python/virtualenvs/python-default/$PY/bin/activate"

for repo_path in $(ls -d ./plugins/*/); do
  pip install -e "$repo_path"
done
