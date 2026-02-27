from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.container_registry.options import (
    ContainerRegistryConditions,
)
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors


async def load_container_registries_by_ids(
    processor: ContainerRegistryProcessors,
    registry_ids: Sequence[uuid.UUID],
) -> list[ContainerRegistryData | None]:
    """Batch load container registries by their IDs.

    Args:
        processor: The container registry processor.
        registry_ids: Sequence of registry UUIDs to load.

    Returns:
        List of ContainerRegistryData (or None if not found) in the same order as registry_ids.
    """
    if not registry_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(registry_ids)),
        conditions=[ContainerRegistryConditions.by_ids(registry_ids)],
    )

    action_result = await processor.search_container_registries.wait_for_complete(
        SearchContainerRegistriesAction(querier=querier)
    )

    registry_map = {registry.id: registry for registry in action_result.data}
    return [registry_map.get(registry_id) for registry_id in registry_ids]
