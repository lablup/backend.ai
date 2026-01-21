from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.repositories.artifact_registry.options import (
    ArtifactRegistryConditions,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors


async def load_artifact_registries_by_ids(
    processor: ArtifactRegistryProcessors,
    registry_ids: Sequence[uuid.UUID],
) -> list[Optional[ArtifactRegistryData]]:
    """Batch load artifact registries by their IDs.

    Args:
        processor: The artifact registry processor.
        registry_ids: Sequence of registry UUIDs to load.

    Returns:
        List of ArtifactRegistryData (or None if not found) in the same order as registry_ids.
    """
    if not registry_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(registry_ids)),
        conditions=[ArtifactRegistryConditions.by_ids(registry_ids)],
    )

    action_result = await processor.search_artifact_registries.wait_for_complete(
        SearchArtifactRegistriesAction(querier=querier)
    )

    registry_map = {registry.id: registry for registry in action_result.registries}
    return [registry_map.get(registry_id) for registry_id in registry_ids]
