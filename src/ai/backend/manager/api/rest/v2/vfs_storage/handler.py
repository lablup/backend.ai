"""REST v2 handlers for the VFS storage domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRootResponseModel,
    BodyParam,
    PathParam,
)
from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    DeleteVFSStorageInput,
    PartialBulkPurgeVFSStoragesInput,
    PartialBulkUpdateVFSStoragesInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    DeleteVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import StorageIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class ListVFSStoragesPayload(BaseRootResponseModel[list[VFSStorageNode]]):
    """Root response model wrapping a list of VFS storage nodes."""

    pass


class V2VFSStorageHandler:
    """REST v2 handler for VFS storage endpoints."""

    def __init__(self, *, adapter: VFSStorageAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateVFSStorageInput],
    ) -> APIResponse:
        """Create a new VFS storage."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def list_all(self) -> APIResponse:
        """List all VFS storages without pagination."""
        items = await self._adapter.list_all()
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=ListVFSStoragesPayload(items),
        )

    async def get(
        self,
        path: PathParam[StorageIdPathParam],
    ) -> APIResponse:
        """Get a single VFS storage by ID."""
        result = await self._adapter.get(path.parsed.storage_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[StorageIdPathParam],
        body: BodyParam[UpdateVFSStorageInput],
    ) -> APIResponse:
        """Update an existing VFS storage. The path ID wins over the ID in the body."""
        result = await self._adapter.update(VFSStorageID(path.parsed.storage_id), body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[StorageIdPathParam],
    ) -> APIResponse:
        """Permanently remove a VFS storage."""
        result = await self._adapter.purge(VFSStorageID(path.parsed.storage_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self,
        body: BodyParam[PartialBulkUpdateVFSStoragesInput],
    ) -> APIResponse:
        """Update several VFS storages, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeVFSStoragesInput],
    ) -> APIResponse:
        """Permanently remove several VFS storages, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search(
        self,
        body: BodyParam[AdminSearchVFSStoragesInput],
    ) -> APIResponse:
        """Search VFS storages with pagination."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteVFSStorageInput],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/vfs-storages/{storage_id}`."""
        purged = await self._adapter.purge(VFSStorageID(body.parsed.id))
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=DeleteVFSStoragePayload(id=purged.id)
        )
