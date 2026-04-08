"""REST v2 handlers for the storage host domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.storage_host import StorageHostAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2StorageHostHandler:
    """REST v2 handler for storage host endpoints."""

    def __init__(self, *, adapter: StorageHostAdapter) -> None:
        self._adapter = adapter

    async def my_storage_host_permissions(self) -> APIResponse:
        """Return the storage hosts and permissions accessible to the current user."""
        result = await self._adapter.my_storage_host_permissions()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
