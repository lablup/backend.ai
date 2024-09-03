#! /bin/bash
if [ ! -d dist/export/python/virtualenvs/python-default ]; then
  >&2 echo "The exported virtualenv does not exist."
  >&2 echo "Please run 'pants export' first and try again."
  exit 1
fi
PYTHON_VERSION=$(cat pants.toml | python3 -c 'import sys,re;m=re.search("CPython==([^\"]+)", sys.stdin.read());print(m.group(1) if m else sys.exit(1))')
if [ $? -ne 0 ]; then
  >&2 echo "Could not read the target CPython interpreter version from pants.toml"
  exit 1
fi
LOCKSET=${LOCKSET:-python-default/$PYTHON_VERSION}
source dist/export/python/virtualenvs/$LOCKSET/bin/activate
PYTHONPATH="src:${PYTHONPATH}" exec python "$@"
