"""Artifact registry metadata adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.dto.manager.v2.artifact_registry.response import ArtifactRegistryGQLNode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.conditions import ArtifactRegistryConditions
from ai.backend.manager.models.artifact_registries.searchers import ArtifactRegistrySearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.lookup import (
    LookupArtifactRegistryAction,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors


class ArtifactRegistryAdapter(BaseAdapter):
    """Adapter for artifact registry metadata operations."""

    _artifact_registry: ArtifactRegistryProcessors

    def __init__(self, artifact_registry: ArtifactRegistryProcessors) -> None:
        self._artifact_registry = artifact_registry

    async def get_registry_meta(
        self, registry_name: str | None = None, registry_id: uuid.UUID | None = None
    ) -> ArtifactRegistryGQLNode:
        """Get metadata for a single artifact registry by id, or by name.

        The two are different reads: an id names the registry, a name resolves to it.
        """
        if registry_id is not None:
            action_result = await self._artifact_registry.get_registry_meta.run(
                GetArtifactRegistryMetaAction(registry_id=ArtifactRegistryID(registry_id))
            )
            return self._data_to_dto(action_result.result)
        if registry_name is None:
            raise InvalidAPIParameters("One of (`registry_id` or `registry_name`) is required")
        resolved = await self._artifact_registry.lookup.run(
            LookupArtifactRegistryAction(name=registry_name)
        )
        action_result = await self._artifact_registry.get_registry_meta.run(
            GetArtifactRegistryMetaAction(registry_id=resolved.entity_id())
        )
        return self._data_to_dto(action_result.result)

    async def get_registry_metas(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ArtifactRegistryGQLNode]:
        """Get metadata for the named artifact registries.

        An id the caller may not read is left out beside one matching no row, so the
        caller cannot tell a denied registry from an absent one.
        """
        result = await self._artifact_registry.get_registry_metas.run(
            GetArtifactRegistryMetasAction(
                registry_ids=[ArtifactRegistryID(registry_id) for registry_id in registry_ids]
            )
        )
        return [self._data_to_dto(item.value) for item in result.items if item.value is not None]

    async def batch_load_by_ids(
        self, ids: Sequence[ArtifactRegistryID]
    ) -> list[ArtifactRegistryGQLNode | None]:
        """Batch load artifact registries by IDs for DataLoader use.

        Returns ArtifactRegistryGQLNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        action_result = await self._artifact_registry.search_artifact_registries.run(
            SearchArtifactRegistriesAction(
                searcher=ArtifactRegistrySearcher(
                    pagination=OffsetPagination(limit=len(ids)),
                    conditions=[ArtifactRegistryConditions.by_ids(ids)],
                )
            )
        )
        registry_map = {item.id: self._data_to_dto(item) for item in action_result.registries}
        return [registry_map.get(ArtifactRegistryID(registry_id)) for registry_id in ids]

    @staticmethod
    def _data_to_dto(data: ArtifactRegistryData) -> ArtifactRegistryGQLNode:
        """Convert data layer type to Pydantic DTO."""
        return ArtifactRegistryGQLNode(
            id=data.id,
            registry_id=ArtifactRegistryID(data.registry_id),
            name=data.name,
            type=data.type,
        )
