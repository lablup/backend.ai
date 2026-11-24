#! /bin/bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
docker buildx build --output "type=local,dest=$SCRIPT_DIR/../../src/ai/backend/runner" \
  "$SCRIPT_DIR/glibc-stub"
