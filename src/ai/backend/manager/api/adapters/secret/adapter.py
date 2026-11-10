"""Adapter for the stored-secret operations, shared by REST v2 and GraphQL."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.secret.response import (
    AdminReencryptSecretsPayload,
    AdminSecretStatusPayload,
    SecretKeyCount,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.secret.types import SecretStatus
from ai.backend.manager.services.secret.actions.reencrypt import ReencryptSecretsAction
from ai.backend.manager.services.secret.actions.status import GetSecretStatusAction
from ai.backend.manager.services.secret.processors import SecretProcessors


class SecretAdapter(BaseAdapter):
    """Adapter for stored secret re-encryption."""

    _secret: SecretProcessors

    def __init__(self, secret: SecretProcessors) -> None:
        self._secret = secret

    async def admin_reencrypt_secrets(self) -> AdminReencryptSecretsPayload:
        """Encrypt every stored secret again through the configured write provider."""
        result = await self._secret.reencrypt.run(ReencryptSecretsAction())
        progress = result.progress
        return AdminReencryptSecretsPayload(
            scanned=progress.scanned,
            reencrypted=progress.reencrypted,
            status=self._status_payload(progress.status),
        )

    async def admin_secret_status(self) -> AdminSecretStatusPayload:
        """Count the stored secrets of every encrypted column by the key holding them."""
        result = await self._secret.get_status.run(GetSecretStatusAction())
        return self._status_payload(result.status)

    def _status_payload(self, status: SecretStatus) -> AdminSecretStatusPayload:
        return AdminSecretStatusPayload(
            write_provider_type=status.write_provider_type.value,
            counts=[
                SecretKeyCount(
                    column=count.column,
                    provider_type=count.provider_type.value,
                    key_id=count.key_id,
                    count=count.count,
                )
                for count in status.counts
            ],
        )
