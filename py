#! /bin/bash
if [ ! -d dist/export/python/virtualenvs/python-default ]; then
  echo "The exported virtualenv does not exist."
  echo "Please run './pants export ::' first and try again."
  exit 1
fi
PYVER=$(python -V | cut -d ' ' -f 2)
LOCKSET=${LOCKSET:-python-default/$PYVER}
source dist/export/python/virtualenvs/$LOCKSET/bin/activate
PYTHONPATH=src python "$@"
