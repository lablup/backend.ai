#! /bin/bash
source dist/export/python/virtualenvs/python-default/*/bin/activate
PYTHONPATH=src python "$@"
