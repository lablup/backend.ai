"""Storage Namespace adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    AdminSearchStorageNamespacesInput,
    RegisterStorageNamespaceInput,
    UnregisterStorageNamespaceInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    AdminSearchStorageNamespacesPayload,
    RegisterStorageNamespacePayload,
    StorageNamespaceNode,
    UnregisterStorageNamespacePayload,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.storage_namespace.conditions import StorageNamespaceConditions
from ai.backend.manager.models.storage_namespace.creators import StorageNamespaceCreator
from ai.backend.manager.repositories.storage_namespace.searchers import StorageNamespaceSearcher
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.lookup import (
    LookupStorageNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)

DEFAULT_PAGINATION_LIMIT = 10


class StorageNamespaceAdapter(BaseAdapter):
    """Adapter for storage namespace domain operations."""

    async def register(
        self, input: RegisterStorageNamespaceInput
    ) -> RegisterStorageNamespacePayload:
        """Register a new namespace within a storage."""
        action_result = await self._processors.storage_namespace.global_register.run(
            RegisterNamespaceAction(
                creator=StorageNamespaceCreator(
                    storage_id=input.storage_id,
                    namespace=input.namespace,
                )
            )
        )
        return RegisterStorageNamespacePayload(
            namespace=self._storage_namespace_data_to_dto(action_result.data)
        )

    async def unregister(
        self, input: UnregisterStorageNamespaceInput
    ) -> UnregisterStorageNamespacePayload:
        """Unregister a namespace from a storage."""
        # The API names a namespace by the pair it was registered under, so the id the
        # purge needs is resolved first rather than taught to the purge itself.
        resolved = await self._processors.storage_namespace.lookup.run(
            LookupStorageNamespaceAction(
                storage_id=input.storage_id,
                namespace=input.namespace,
            )
        )
        action_result = await self._processors.storage_namespace.unregister.run(
            UnregisterNamespaceAction(id=resolved.data.id)
        )
        return UnregisterStorageNamespacePayload(id=action_result.data.storage_id)

    async def get_namespaces(self, storage_id: uuid.UUID) -> list[StorageNamespaceNode]:
        """Retrieve all namespaces for a given storage."""
        action_result = await self._processors.storage_namespace.global_get_namespaces.run(
            GetNamespacesAction(storage_id)
        )
        return [self._storage_namespace_data_to_dto(item) for item in action_result.items]

    async def batch_load_by_ids(
        self, ids: Sequence[uuid.UUID]
    ) -> list[StorageNamespaceNode | None]:
        """Batch load storage namespaces by IDs for DataLoader use.

        Returns StorageNamespaceNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        searcher = StorageNamespaceSearcher(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[StorageNamespaceConditions.by_ids(ids)],
        )
        action_result = await self._processors.storage_namespace.global_search.run(
            SearchStorageNamespacesAction(searcher=searcher)
        )
        namespace_map = {
            item.id: self._storage_namespace_data_to_dto(item) for item in action_result.items
        }
        return [namespace_map.get(StorageNamespaceID(namespace_id)) for namespace_id in ids]

    async def search(
        self, input: AdminSearchStorageNamespacesInput
    ) -> AdminSearchStorageNamespacesPayload:
        """Search storage namespaces with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        searcher = StorageNamespaceSearcher(conditions=[], orders=[], pagination=pagination)
        action_result = await self._processors.storage_namespace.global_search.run(
            SearchStorageNamespacesAction(searcher=searcher)
        )
        return AdminSearchStorageNamespacesPayload(
            items=[self._storage_namespace_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    @staticmethod
    def _storage_namespace_data_to_dto(data: StorageNamespaceData) -> StorageNamespaceNode:
        return StorageNamespaceNode(
            id=data.id,
            storage_id=data.storage_id,
            namespace=data.namespace,
        )
