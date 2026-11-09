"""V2 REST SDK client for the VFS storage resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.api_handlers import BaseRootResponseModel
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    DeleteVFSStorageInput,
    PartialBulkPurgeVFSStoragesInput,
    PartialBulkUpdateVFSStoragesInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    AdminSearchVFSStoragesPayload,
    CreateVFSStoragePayload,
    DeleteVFSStoragePayload,
    PurgeVFSStoragePayload,
    UpdateVFSStoragePayload,
    VFSStorageNode,
)

_PATH = "/v2/vfs-storages"


class _ListVFSStoragesPayload(BaseRootResponseModel[list[VFSStorageNode]]):
    """Root response model wrapping a list of VFS storage nodes."""

    pass


class V2VFSStorageClient(BaseDomainClient):
    """SDK client for ``/v2/vfs-storages`` endpoints."""

    async def create(self, request: CreateVFSStorageInput) -> CreateVFSStoragePayload:
        """Create a new VFS storage."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateVFSStoragePayload,
        )

    async def list_all(self) -> _ListVFSStoragesPayload:
        """List all VFS storages without pagination."""
        return await self._client.typed_request(
            "GET",
            _PATH,
            response_model=_ListVFSStoragesPayload,
        )

    async def get(self, storage_id: UUID) -> VFSStorageNode:
        """Retrieve a single VFS storage by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{storage_id}",
            response_model=VFSStorageNode,
        )

    async def update(self, request: UpdateVFSStorageInput) -> UpdateVFSStoragePayload:
        """Update an existing VFS storage."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{request.id}",
            request=request,
            response_model=UpdateVFSStoragePayload,
        )

    async def search(
        self,
        request: AdminSearchVFSStoragesInput,
    ) -> AdminSearchVFSStoragesPayload:
        """Search VFS storages with pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchVFSStoragesPayload,
        )

    async def delete(self, request: DeleteVFSStorageInput) -> DeleteVFSStoragePayload:
        """Deprecated. Use :meth:`purge`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteVFSStoragePayload,
        )

    async def purge(self, storage_id: UUID) -> PurgeVFSStoragePayload:
        """Permanently remove a VFS storage."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{storage_id}",
            response_model=PurgeVFSStoragePayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateVFSStoragesInput
    ) -> PartialBulkPayload[VFSStorageNode]:
        """Update several VFS storages, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[VFSStorageNode],
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeVFSStoragesInput
    ) -> PartialBulkPayload[VFSStorageNode]:
        """Permanently remove several VFS storages, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[VFSStorageNode],
        )
