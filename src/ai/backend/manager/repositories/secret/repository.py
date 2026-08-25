from __future__ import annotations

from ai.backend.manager.data.secret.types import SecretSweepProgress, SecretSweepStatus
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.secret.db_source.db_source import SecretDBSource
from ai.backend.manager.secret.pool import KeyProviderPool


class SecretRepository:
    """Encrypts stored secrets again through the configured write provider.

    The two caller-facing operations are :meth:`reencrypt_keypair_secrets`, a chunked
    pass over ``keypairs.secret_key``, and :meth:`keypair_secret_status`, which counts
    what each key holds.
    """

    _db_source: SecretDBSource

    def __init__(self, ops_provider: SecretOpsProvider, key_provider_pool: KeyProviderPool) -> None:
        self._db_source = SecretDBSource(ops_provider, key_provider_pool)

    async def reencrypt_keypair_secrets(self) -> SecretSweepProgress:
        return await self._db_source.reencrypt_keypair_secrets()

    async def keypair_secret_status(self) -> SecretSweepStatus:
        return await self._db_source.keypair_secret_status()
