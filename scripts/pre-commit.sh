#! /bin/bash
# implementation: backend.ai monorepo standard pre-commit hook
BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
echo "Performing lint for changed files ..."
if [ -f .pants.rc ]; then
  source scripts/bootstrap-static-python.sh
  local_exec_root_dir=$($bpython scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')
  mkdir -p "$local_exec_root_dir"
fi
pants lint --changed-since="HEAD~1"
