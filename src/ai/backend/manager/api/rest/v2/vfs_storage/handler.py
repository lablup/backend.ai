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
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    DeleteVFSStorageInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import VFSStorageNode
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import StorageIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.vfs_storage import VFSStorageAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
        body: BodyParam[UpdateVFSStorageInput],
    ) -> APIResponse:
        """Update an existing VFS storage."""
        result = await self._adapter.update(body.parsed)
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
        """Delete a VFS storage."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
