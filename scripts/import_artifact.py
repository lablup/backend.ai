"""
Artifact import script.

1. Search model artifacts from the artifact registry.
2. Pick the smallest revision by size.
3. Call import_artifacts to start downloading it.

Usage:
    python scripts/import_artifact.py \
        --endpoint http://127.0.0.1:8091 \
        --access-key AKIAIOSFODNN7EXAMPLE \
        --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from yarl import URL

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.artifact import ArtifactClient
from ai.backend.client.v2.domains.artifact_registry import ArtifactRegistryClient
from ai.backend.common.dto.manager.artifact.request import ImportArtifactsRequest
from ai.backend.common.dto.manager.artifact_registry.request import (
    ArtifactFilterInput,
    OffsetPaginationInput,
    PaginationInput,
    SearchArtifactsRequest,
)


async def run(endpoint: str, access_key: str, secret_key: str) -> None:
    config = ClientConfig(endpoint=URL(endpoint))
    auth = HMACAuth(access_key=access_key, secret_key=secret_key)
    client = await BackendAIAuthClient.create(config, auth)

    try:
        artifact_registry_client = ArtifactRegistryClient(client)
        artifact_client = ArtifactClient(client)

        # Step 1: Search model artifacts
        print("Searching for model artifacts...")
        search_response = await artifact_registry_client.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=100),
                ),
                filters=ArtifactFilterInput(
                    artifact_type=["MODEL"],
                ),
            ),
        )

        if not search_response.artifacts:
            print("No model artifacts found.")
            return

        # Step 2: Collect all revisions with size info, pick the smallest
        candidates: list[tuple[int, str, str, object]] = []  # (size, name, version, revision)

        for artifact in search_response.artifacts:
            print(
                f"  Artifact: {artifact.name} (id={artifact.id}, type={artifact.type},"
                f" revisions={len(artifact.revisions)})"
            )
            for revision in artifact.revisions:
                size_display = (
                    f"{revision.size / 1024 / 1024:.1f} MB" if revision.size else "unknown"
                )
                print(
                    f"    Revision: {revision.version} (id={revision.id},"
                    f" status={revision.status}, size={size_display})"
                )
                if revision.size is not None and revision.size > 0:
                    candidates.append(
                        (revision.size, artifact.name, revision.version, revision)
                    )

        if not candidates:
            print("No revisions with known size found.")
            return

        # Sort by size ascending and pick the smallest
        candidates.sort(key=lambda candidate: candidate[0])
        smallest_size, smallest_artifact_name, smallest_version, smallest_revision = candidates[0]
        print(
            f"\nSmallest model: {smallest_artifact_name} revision: {smallest_version}"
            f" (size={smallest_size / 1024 / 1024:.1f} MB)"
        )

        # Step 3: Import the smallest artifact
        print(f"Importing revision id={smallest_revision.id} ...")
        import_response = await artifact_client.import_artifacts(
            ImportArtifactsRequest(
                artifact_revision_ids=[smallest_revision.id],
            ),
        )

        print("Import started successfully!")
        for task in import_response.tasks:
            print(f"  Task ID: {task.task_id}")
            print(
                f"  Revision: {task.artifact_revision.version}"
                f" (status={task.artifact_revision.status})"
            )
        print("\nFull response:")
        print(json.dumps(import_response.model_dump(mode="json"), indent=2, default=str))

    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import an artifact from Backend.AI")
    parser.add_argument(
        "--endpoint",
        default="http://110.45.167.85:8091",
        help="Manager API endpoint (default: http://110.45.167.85:8091)",
    )
    parser.add_argument("--access-key", required=True, help="API access key")
    parser.add_argument("--secret-key", required=True, help="API secret key")
    arguments = parser.parse_args()

    asyncio.run(run(arguments.endpoint, arguments.access_key, arguments.secret_key))


if __name__ == "__main__":
    main()
