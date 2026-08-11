import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.services.storage_namespace.actions.get_all import (
    GetAllNamespacesAction,
    GetAllNamespacesActionResult,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
    UnregisterNamespaceActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StorageNamespaceService:
    _storage_namespace_repository: StorageNamespaceRepository

    def __init__(
        self,
        storage_namespace_repository: StorageNamespaceRepository,
    ) -> None:
        self._storage_namespace_repository = storage_namespace_repository

    async def unregister(
        self, action: UnregisterNamespaceAction
    ) -> UnregisterNamespaceActionResult:
        log.info("Unregistering storage namespace")
        storage_id = await self._storage_namespace_repository.unregister(
            action.storage_id, action.namespace
        )
        return UnregisterNamespaceActionResult(storage_id=storage_id)

    async def get_all_namespaces(
        self, _action: GetAllNamespacesAction
    ) -> GetAllNamespacesActionResult:
        log.info("Getting all namespaces grouped by storage")
        namespaces_by_storage = (
            await self._storage_namespace_repository.get_all_namespaces_by_storage()
        )
        return GetAllNamespacesActionResult(result=namespaces_by_storage)
