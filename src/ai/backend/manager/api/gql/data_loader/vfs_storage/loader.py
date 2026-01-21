from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfs_storage.options import VFSStorageConditions
from ai.backend.manager.services.vfs_storage.actions.search import SearchVFSStoragesAction
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors


async def load_vfs_storages_by_ids(
    processor: VFSStorageProcessors,
    storage_ids: Sequence[uuid.UUID],
) -> list[Optional[VFSStorageData]]:
    """Batch load VFS storages by their IDs.

    Args:
        processor: The VFS storage processor.
        storage_ids: Sequence of storage UUIDs to load.

    Returns:
        List of VFSStorageData (or None if not found) in the same order as storage_ids.
    """
    if not storage_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(storage_ids)),
        conditions=[VFSStorageConditions.by_ids(storage_ids)],
    )

    action_result = await processor.search_vfs_storages.wait_for_complete(
        SearchVFSStoragesAction(querier=querier)
    )

    storage_map = {storage.id: storage for storage in action_result.storages}
    return [storage_map.get(storage_id) for storage_id in storage_ids]
