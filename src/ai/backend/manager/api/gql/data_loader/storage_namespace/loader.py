from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.storage_namespace.options import StorageNamespaceConditions
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors


async def load_storage_namespaces_by_ids(
    processor: StorageNamespaceProcessors,
    namespace_ids: Sequence[uuid.UUID],
) -> list[Optional[StorageNamespaceData]]:
    """Batch load storage namespaces by their IDs.

    Args:
        processor: The storage namespace processor.
        namespace_ids: Sequence of namespace UUIDs to load.

    Returns:
        List of StorageNamespaceData (or None if not found) in the same order as namespace_ids.
    """
    if not namespace_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(namespace_ids)),
        conditions=[StorageNamespaceConditions.by_ids(namespace_ids)],
    )

    action_result = await processor.search_storage_namespaces.wait_for_complete(
        SearchStorageNamespacesAction(querier=querier)
    )

    namespace_map = {namespace.id: namespace for namespace in action_result.namespaces}
    return [namespace_map.get(namespace_id) for namespace_id in namespace_ids]
