"""REST v2 handlers for the object storage domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    UpdateObjectStorageInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import StorageIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.object_storage import ObjectStorageAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ObjectStorageHandler:
    """REST v2 handler for object storage endpoints."""

    def __init__(self, *, adapter: ObjectStorageAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateObjectStorageInput],
    ) -> APIResponse:
        """Create a new object storage."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[StorageIdPathParam],
    ) -> APIResponse:
        """Get a single object storage by ID."""
        result = await self._adapter.get(path.parsed.storage_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        body: BodyParam[UpdateObjectStorageInput],
    ) -> APIResponse:
        """Update an existing object storage."""
        result = await self._adapter.update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search(
        self,
        body: BodyParam[AdminSearchObjectStoragesInput],
    ) -> APIResponse:
        """Search object storages with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteObjectStorageInput],
    ) -> APIResponse:
        """Delete an object storage."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
