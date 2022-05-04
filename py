#! /bin/bash
if [ ! -d dist/export/python/virtualenvs/python-default ]; then
  echo "The exported virtualenv does not exist."
  echo "Please run './pants export ::' first and try again."
  exit 1
fi
source dist/export/python/virtualenvs/python-default/*/bin/activate
PYTHONPATH=src python "$@"
