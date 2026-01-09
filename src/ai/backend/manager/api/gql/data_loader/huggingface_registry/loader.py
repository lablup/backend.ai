from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.huggingface_registry.options import (
    HuggingFaceRegistryConditions,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors


async def load_huggingface_registries_by_ids(
    processor: ArtifactRegistryProcessors,
    registry_ids: Sequence[uuid.UUID],
) -> list[Optional[HuggingFaceRegistryData]]:
    """Batch load HuggingFace registries by their IDs.

    Args:
        processor: The artifact registry processor.
        registry_ids: Sequence of registry UUIDs to load.

    Returns:
        List of HuggingFaceRegistryData (or None if not found) in the same order as registry_ids.
    """
    if not registry_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(registry_ids)),
        conditions=[HuggingFaceRegistryConditions.by_ids(registry_ids)],
    )

    action_result = await processor.search_huggingface_registries.wait_for_complete(
        SearchHuggingFaceRegistriesAction(querier=querier)
    )

    registry_map = {registry.id: registry for registry in action_result.registries}
    return [registry_map.get(registry_id) for registry_id in registry_ids]
