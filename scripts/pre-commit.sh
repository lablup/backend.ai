# implementation: backend.ai monorepo standard pre-commit hook
echo "Performing lint for changed files ..."
local_exec_root_dir=$(python scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')
mkdir -p "$local_exec_root_dir"
pants lint --changed-since="HEAD~1"
