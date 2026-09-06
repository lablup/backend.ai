"""V2 SDK client for the stored secret domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.secret.response import (
    AdminReencryptSecretsPayload,
    AdminSecretStatusPayload,
)

_PATH: Final = "/v2/secrets"


class V2SecretClient(BaseDomainClient):
    """SDK client for the stored secret operations."""

    async def admin_reencrypt(self) -> AdminReencryptSecretsPayload:
        """Encrypt every stored secret again through the write provider (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/reencrypt",
            response_model=AdminReencryptSecretsPayload,
        )

    async def admin_status(self) -> AdminSecretStatusPayload:
        """Report the stored secrets per column and key id (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/status",
            response_model=AdminSecretStatusPayload,
        )
