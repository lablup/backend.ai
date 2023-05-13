# implementation: backend.ai monorepo standard pre-commit hook
BASE_PATH=$(pwd)
echo "Performing lint for changed files ..."
pants lint --changed-since="HEAD~1"
