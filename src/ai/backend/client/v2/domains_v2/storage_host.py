"""V2 REST SDK client for the storage host resource."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
)

_PATH = "/v2/storage-hosts"


class V2StorageHostClient(BaseDomainClient):
    """SDK client for ``/v2/storage-hosts`` endpoints."""

    async def my_storage_host_permissions(self) -> MyStorageHostPermissionsPayload:
        """Return the storage hosts and permissions accessible to the current user."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/my/permissions",
            response_model=MyStorageHostPermissionsPayload,
        )
