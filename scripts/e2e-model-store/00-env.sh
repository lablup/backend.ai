#!/bin/bash
# Common environment for model store E2E tests.
# Source this file before running any scenario.
#
# Usage: source scripts/e2e-model-store/00-env.sh

set -euo pipefail

BAI="./bai"
PY="./py"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Legacy CLI env vars for vfolder upload
export BACKEND_ENDPOINT="http://127.0.0.1:8091"
export BACKEND_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
export BACKEND_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Discover IDs from the running system
export VLLM_VARIANT_ID=$($BAI admin runtime-variant search --name-contains vllm 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")

export IMAGE_ID=$($BAI admin image search --limit 1 2>&1 \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")

export MODEL_VFOLDER_ID=$($PY -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:develove@localhost:8101/backend')
    async with engine.begin() as conn:
        result = await conn.execute(sa.text(\"SELECT id FROM vfolders WHERE usage_mode = 'model' LIMIT 1\"))
        row = result.fetchone()
        print(row[0] if row else '')
asyncio.run(main())
" 2>&1)

export MODEL_VFOLDER_NAME=$($PY -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:develove@localhost:8101/backend')
    async with engine.begin() as conn:
        result = await conn.execute(sa.text(\"SELECT name FROM vfolders WHERE usage_mode = 'model' LIMIT 1\"))
        row = result.fetchone()
        print(row[0] if row else '')
asyncio.run(main())
" 2>&1)

export RESOURCE_GROUP="default"
export DOMAIN_NAME="default"
export PROJECT_ID=$($PY -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy as sa
async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:develove@localhost:8101/backend')
    async with engine.begin() as conn:
        result = await conn.execute(sa.text(\"SELECT id FROM groups WHERE type = 'model-store' LIMIT 1\"))
        row = result.fetchone()
        print(row[0] if row else '')
asyncio.run(main())
" 2>&1)

# Upload serve.py to model vfolder for health check
echo "Uploading serve.py to model vfolder ($MODEL_VFOLDER_NAME)..."
./backend.ai vfolder upload "$MODEL_VFOLDER_NAME" "$SCRIPT_DIR/test-model/serve.py" 2>&1 | tail -1

echo "=== Model Store E2E Environment ==="
echo "  VLLM_VARIANT_ID:   $VLLM_VARIANT_ID"
echo "  IMAGE_ID:          $IMAGE_ID"
echo "  MODEL_VFOLDER_ID:  $MODEL_VFOLDER_ID"
echo "  MODEL_VFOLDER_NAME:$MODEL_VFOLDER_NAME"
echo "  RESOURCE_GROUP:    $RESOURCE_GROUP"
echo "  PROJECT_ID:        $PROJECT_ID"
echo "  DOMAIN_NAME:       $DOMAIN_NAME"
echo "==================================="
