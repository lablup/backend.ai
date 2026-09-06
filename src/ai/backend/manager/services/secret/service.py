from __future__ import annotations

from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.services.secret.actions.reencrypt import (
    ReencryptSecretsAction,
    ReencryptSecretsActionResult,
)
from ai.backend.manager.services.secret.actions.status import (
    GetSecretStatusAction,
    GetSecretStatusActionResult,
)


class SecretService:
    _secret_repository: SecretRepository

    def __init__(self, secret_repository: SecretRepository) -> None:
        self._secret_repository = secret_repository

    async def reencrypt(self, action: ReencryptSecretsAction) -> ReencryptSecretsActionResult:
        return ReencryptSecretsActionResult(progress=await self._secret_repository.reencrypt())

    async def get_status(self, action: GetSecretStatusAction) -> GetSecretStatusActionResult:
        return GetSecretStatusActionResult(status=await self._secret_repository.status())
