"""V2 REST SDK client for the storage namespace resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.api_handlers import BaseRootResponseModel
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

_PATH = "/v2/storage-namespaces"


class _ListStorageNamespacesPayload(BaseRootResponseModel[list[StorageNamespaceNode]]):
    """Root response model wrapping a list of storage namespace nodes."""

    pass


class V2StorageNamespaceClient(BaseDomainClient):
    """SDK client for ``/v2/storage-namespaces`` endpoints."""

    async def register(
        self,
        request: RegisterStorageNamespaceInput,
    ) -> RegisterStorageNamespacePayload:
        """Register a new namespace within a storage."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=RegisterStorageNamespacePayload,
        )

    async def unregister(
        self,
        request: UnregisterStorageNamespaceInput,
    ) -> UnregisterStorageNamespacePayload:
        """Unregister a namespace from a storage."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/unregister",
            request=request,
            response_model=UnregisterStorageNamespacePayload,
        )

    async def search(
        self,
        request: AdminSearchStorageNamespacesInput,
    ) -> AdminSearchStorageNamespacesPayload:
        """Search storage namespaces with pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchStorageNamespacesPayload,
        )

    async def get_by_storage(
        self,
        storage_id: UUID,
    ) -> _ListStorageNamespacesPayload:
        """Get all namespaces for a given storage."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/by-storage/{storage_id}",
            response_model=_ListStorageNamespacesPayload,
        )
