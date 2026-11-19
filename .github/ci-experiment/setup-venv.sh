#!/usr/bin/env bash
#
# Build a virtualenv holding the python-default resolve at the versions python.lock pins.
#
#   setup-venv.sh <python-version> <venv-dir> <work-dir>
#
# Installs the requirements the lock was generated from, constrained to the locked
# versions, plus pytest-xdist and pytest-rerunfailures, which the lock does not hold.
# Prints the number of installed packages whose version differs from the lock.
set -euo pipefail

python=$1
venv=$2
work=$3
here=$(dirname "$0")

mkdir -p "$work"
"$here/exp.py" requirements python.lock.metadata > "$work/requirements.txt"
"$here/exp.py" pins python.lock > "$work/constraints.txt"
uv venv --python "$python" "$venv" >&2
uv pip install --python "$venv/bin/python" -r "$work/requirements.txt" -c "$work/constraints.txt" \
  -r "$here/requirements-extra.txt" >&2
uv pip freeze --python "$venv/bin/python" > "$work/freeze.txt"
# A package the lock pins at another version.
sort "$work/constraints.txt" | tr 'A-Z_.' 'a-z--' > "$work/pins.sorted"
sort "$work/freeze.txt" | tr 'A-Z_.' 'a-z--' > "$work/freeze.sorted"
comm -13 "$work/pins.sorted" "$work/freeze.sorted" | tee "$work/unpinned.txt" >&2
wc -l < "$work/unpinned.txt" | tr -d ' '
