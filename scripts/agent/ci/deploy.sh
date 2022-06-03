#! /bin/bash
set -ev

pip install --user -U twine setuptools wheel
python setup.py sdist bdist_wheel
twine upload dist/*
