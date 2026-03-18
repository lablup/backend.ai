"""Storage Namespace adapter bridging DTOs and Processors."""

from __future__ import annotations

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
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.storage_namespace import StorageNamespaceCreatorSpec
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class StorageNamespaceAdapter(BaseAdapter):
    """Adapter for storage namespace domain operations."""

    async def register(
        self, input: RegisterStorageNamespaceInput
    ) -> RegisterStorageNamespacePayload:
        """Register a new namespace within a storage."""
        action_result = await self._processors.storage_namespace.register.wait_for_complete(
            RegisterNamespaceAction(
                creator=Creator(
                    spec=StorageNamespaceCreatorSpec(
                        storage_id=input.storage_id,
                        bucket=input.namespace,
                    )
                )
            )
        )
        return RegisterStorageNamespacePayload(
            namespace=self._storage_namespace_data_to_dto(action_result.result)
        )

    async def unregister(
        self, input: UnregisterStorageNamespaceInput
    ) -> UnregisterStorageNamespacePayload:
        """Unregister a namespace from a storage."""
        action_result = await self._processors.storage_namespace.unregister.wait_for_complete(
            UnregisterNamespaceAction(
                storage_id=input.storage_id,
                namespace=input.namespace,
            )
        )
        return UnregisterStorageNamespacePayload(id=action_result.storage_id)

    async def search(
        self, input: AdminSearchStorageNamespacesInput
    ) -> AdminSearchStorageNamespacesPayload:
        """Search storage namespaces with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        querier = BatchQuerier(conditions=[], orders=[], pagination=pagination)
        action_result = (
            await self._processors.storage_namespace.search_storage_namespaces.wait_for_complete(
                SearchStorageNamespacesAction(querier=querier)
            )
        )
        return AdminSearchStorageNamespacesPayload(
            items=[self._storage_namespace_data_to_dto(item) for item in action_result.namespaces],
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
