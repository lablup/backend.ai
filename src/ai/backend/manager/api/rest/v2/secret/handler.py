"""REST v2 handler for the stored-secret operations."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.secret.adapter import SecretAdapter


class V2SecretHandler:
    """REST v2 handler for stored secret re-encryption."""

    def __init__(self, *, adapter: SecretAdapter) -> None:
        self._adapter = adapter

    async def admin_reencrypt(self) -> APIResponse:
        """Encrypt every stored secret again through the write provider (superadmin only)."""
        result = await self._adapter.admin_reencrypt_secrets()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_status(self) -> APIResponse:
        """Report the stored secrets per column and key id (superadmin only)."""
        result = await self._adapter.admin_secret_status()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
