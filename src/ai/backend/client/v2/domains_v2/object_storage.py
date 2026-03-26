"""V2 REST SDK client for the object storage resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    UpdateObjectStorageInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    AdminSearchObjectStoragesPayload,
    CreateObjectStoragePayload,
    DeleteObjectStoragePayload,
    ObjectStorageNode,
    UpdateObjectStoragePayload,
)

_PATH = "/v2/object-storages"


class V2ObjectStorageClient(BaseDomainClient):
    """SDK client for ``/v2/object-storages`` endpoints."""

    async def create(
        self,
        request: CreateObjectStorageInput,
    ) -> CreateObjectStoragePayload:
        """Create a new object storage."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateObjectStoragePayload,
        )

    async def get(self, storage_id: UUID) -> ObjectStorageNode:
        """Retrieve a single object storage by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{storage_id}",
            response_model=ObjectStorageNode,
        )

    async def update(
        self,
        request: UpdateObjectStorageInput,
    ) -> UpdateObjectStoragePayload:
        """Update an existing object storage."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{request.id}",
            request=request,
            response_model=UpdateObjectStoragePayload,
        )

    async def search(
        self,
        request: AdminSearchObjectStoragesInput,
    ) -> AdminSearchObjectStoragesPayload:
        """Search object storages with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchObjectStoragesPayload,
        )

    async def delete(
        self,
        request: DeleteObjectStorageInput,
    ) -> DeleteObjectStoragePayload:
        """Delete an object storage."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteObjectStoragePayload,
        )
