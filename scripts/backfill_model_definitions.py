"""
Backfill model_definition in deployment_revisions for pre-26.4.2 endpoints.

During the 26.4.2 migration (25ac68cb28ba), deployment revision rows were created
with model_definition = NULL because the migration cannot access storage backends.
This script calls modify_endpoint (GQL) for each endpoint, which triggers
model_definition resolution for revisions that have NULL model_definition.

Prerequisites:
  - Backend.AI manager running and accessible
  - Superadmin credentials (access key / secret key)

Usage:
  export BAI_ENDPOINT="http://127.0.0.1:8091"
  export BAI_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
  export BAI_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

  python scripts/backfill_model_definitions.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Any
from uuid import UUID

from yarl import URL

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.deployment import (
    ListDeploymentsResponse,
    SearchDeploymentsRequest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

MODIFY_ENDPOINT_MUTATION = """
mutation($endpoint_id: UUID!, $props: ModifyEndpointInput!) {
    modify_endpoint(endpoint_id: $endpoint_id, props: $props) {
        ok
        msg
    }
}
"""


async def gql_modify_endpoint(
    registry: BackendAIClientRegistry,
    endpoint_id: UUID,
) -> dict[str, Any]:
    """Call the GQL ModifyEndpoint mutation with empty props (no-op update)."""
    payload = {
        "query": MODIFY_ENDPOINT_MUTATION,
        "variables": {
            "endpoint_id": str(endpoint_id),
            "props": {},
        },
    }
    result = await registry._client._request("POST", "/admin/graphql", json=payload)
    return result


async def fetch_all_deployment_ids(
    registry: BackendAIClientRegistry,
) -> list[UUID]:
    """Fetch all deployment IDs via REST v2 search API."""
    deployment_ids: list[UUID] = []
    offset = 0
    limit = 100

    while True:
        request = SearchDeploymentsRequest(limit=limit, offset=offset)
        response: ListDeploymentsResponse = await registry._client.typed_request(
            "POST",
            "/v2/deployments/search",
            request=request,
            response_model=ListDeploymentsResponse,
        )
        for deployment in response.deployments:
            deployment_ids.append(deployment.id)

        if not response.pagination.has_next_page:
            break
        offset += limit

    return deployment_ids


async def backfill_model_definitions(*, dry_run: bool = False) -> None:
    endpoint = os.environ.get("BAI_ENDPOINT")
    access_key = os.environ.get("BAI_ACCESS_KEY")
    secret_key = os.environ.get("BAI_SECRET_KEY")

    if not all([endpoint, access_key, secret_key]):
        log.error("BAI_ENDPOINT, BAI_ACCESS_KEY, BAI_SECRET_KEY must be set.")
        sys.exit(1)

    config = ClientConfig(endpoint=URL(endpoint), endpoint_type="api")
    auth = HMACAuth(access_key=access_key, secret_key=secret_key)
    registry = await BackendAIClientRegistry.create(config, auth)

    try:
        deployment_ids = await fetch_all_deployment_ids(registry)
        total = len(deployment_ids)
        log.info(f"Found {total} deployment(s).")

        if total == 0:
            return

        succeeded = 0
        failed = 0

        for i, deployment_id in enumerate(deployment_ids, 1):
            if dry_run:
                log.info(f"[dry-run] [{i}/{total}] Would call modify_endpoint for {deployment_id}")
                succeeded += 1
                continue

            try:
                result = await gql_modify_endpoint(registry, deployment_id)
                data = result.get("data", {}).get("modify_endpoint", {})
                if data.get("ok"):
                    log.info(f"[{i}/{total}] {deployment_id} — ok")
                    succeeded += 1
                else:
                    msg = data.get("msg", "unknown error")
                    log.warning(f"[{i}/{total}] {deployment_id} — failed: {msg}")
                    failed += 1
            except Exception as e:
                log.warning(f"[{i}/{total}] {deployment_id} — error: {e}")
                failed += 1

        log.info(f"Backfill complete. Succeeded: {succeeded}, Failed: {failed}")
    finally:
        await registry.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill model_definition in deployment_revisions for legacy endpoints.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes.",
    )
    args = parser.parse_args()
    asyncio.run(backfill_model_definitions(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
