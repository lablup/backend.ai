"""V2 REST SDK client for the artifact registry resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.artifact_registry.response import (
    ArtifactRegistryGQLNode,
)

_PATH = "/v2/artifact-registries"


class V2ArtifactRegistryClient(BaseDomainClient):
    """SDK client for ``/v2/artifact-registries`` endpoints."""

    async def get_registry_meta(self, registry_id: UUID) -> ArtifactRegistryGQLNode:
        """Get metadata for a single artifact registry by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{registry_id}",
            response_model=ArtifactRegistryGQLNode,
        )
