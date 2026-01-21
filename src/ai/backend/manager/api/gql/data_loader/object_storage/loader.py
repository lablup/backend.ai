from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.object_storage.options import ObjectStorageConditions
from ai.backend.manager.services.object_storage.actions.search import SearchObjectStoragesAction
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors


async def load_object_storages_by_ids(
    processor: ObjectStorageProcessors,
    storage_ids: Sequence[uuid.UUID],
) -> list[Optional[ObjectStorageData]]:
    """Batch load object storages by their IDs.

    Args:
        processor: The object storage processor.
        storage_ids: Sequence of object storage UUIDs to load.

    Returns:
        List of ObjectStorageData (or None if not found) in the same order as storage_ids.
    """
    if not storage_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(storage_ids)),
        conditions=[ObjectStorageConditions.by_ids(storage_ids)],
    )

    action_result = await processor.search_object_storages.wait_for_complete(
        SearchObjectStoragesAction(querier=querier)
    )

    storage_map = {storage.id: storage for storage in action_result.storages}
    return [storage_map.get(storage_id) for storage_id in storage_ids]
