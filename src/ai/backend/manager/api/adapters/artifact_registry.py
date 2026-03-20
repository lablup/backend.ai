"""Artifact registry metadata adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.artifact_registry.response import ArtifactRegistryGQLNode
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)

from .base import BaseAdapter


class ArtifactRegistryAdapter(BaseAdapter):
    """Adapter for artifact registry metadata operations."""

    async def get_registry_meta(
        self, registry_name: str | None = None, registry_id: uuid.UUID | None = None
    ) -> ArtifactRegistryGQLNode:
        """Get metadata for a single artifact registry by name or ID."""
        action_result = (
            await self._processors.artifact_registry.get_registry_meta.wait_for_complete(
                GetArtifactRegistryMetaAction(
                    registry_name=registry_name,
                    registry_id=registry_id,
                )
            )
        )
        return self._data_to_dto(action_result.result)

    async def get_registry_metas(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ArtifactRegistryGQLNode]:
        """Get metadata for multiple artifact registries by IDs."""
        action_result = (
            await self._processors.artifact_registry.get_registry_metas.wait_for_complete(
                GetArtifactRegistryMetasAction(registry_ids=registry_ids)
            )
        )
        return [self._data_to_dto(item) for item in action_result.result]

    @staticmethod
    def _data_to_dto(data: ArtifactRegistryData) -> ArtifactRegistryGQLNode:
        """Convert data layer type to Pydantic DTO."""
        return ArtifactRegistryGQLNode(
            id=data.id,
            registry_id=data.registry_id,
            name=data.name,
            type=data.type,
        )
