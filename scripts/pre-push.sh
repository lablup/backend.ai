# backend.ai monorepo standard pre-push hook
BASEPATH=$(cd "$(dirname "$0")"/../.. && pwd)
if [ -f "$BASEPATH/pants-local" ]; then
    PANTS=$BASEPATH/pants-local
else
    PANTS=$BASEPATH/pants
fi
set -ex
$PANTS fmt ::
$PANTS lint check --changed-since=$(git merge-base main HEAD)
$PANTS tailor --check
