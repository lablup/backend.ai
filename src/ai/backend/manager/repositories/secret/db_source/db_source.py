"""Database source for the stored-secret re-encryption pass.

Walks ``keypairs.secret_key`` in access key order, chunk by chunk, and encrypts every
value again through the write provider under a fresh data encryption key. Every row is
treated alike, whatever key it was on: a pass interrupted halfway is resumed by running
it again.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from typing import Final

from ai.backend.common.types import AccessKey
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.secret.types import (
    KeyProviderType,
    SecretKeyId,
    SecretKeyIdCount,
    SecretSweepProgress,
    SecretSweepStatus,
)
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.secret.pool import KeyProviderPool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Rows one chunk reads and writes back in a single transaction, so a large table
# never becomes one long-held transaction.
_CHUNK_SIZE: Final[int] = 1000


class SecretDBSource:
    _ops: SecretOpsProvider
    _key_provider_pool: KeyProviderPool

    def __init__(self, ops_provider: SecretOpsProvider, key_provider_pool: KeyProviderPool) -> None:
        self._ops = ops_provider
        self._key_provider_pool = key_provider_pool

    async def reencrypt_keypair_secrets(self) -> SecretSweepProgress:
        """Encrypt every stored secret again through the write provider.

        Each chunk reads its rows and writes them back in the same transaction, and every
        write carries the value it read as its condition, so a keypair reissued mid-pass
        keeps the new secret and the stale value is dropped.
        """
        cursor: AccessKey | None = None
        scanned = 0
        reencrypted = 0
        while True:
            async with self._ops.write_ops() as w:
                stored = await w.scan_keypair_secrets(cursor, _CHUNK_SIZE)
                for secret in stored:
                    scanned += 1
                    cursor = secret.access_key
                    replacement = await self._key_provider_pool.reencrypt(
                        secret.value, KEYPAIR_SECRET_KEY_CONTEXT
                    )
                    if await w.rewrite_keypair_secret(secret.access_key, secret.value, replacement):
                        reencrypted += 1
            if len(stored) < _CHUNK_SIZE:
                break
        log.info(
            "secret re-encryption read {} keypair secret(s) and wrote {}", scanned, reencrypted
        )
        return SecretSweepProgress(
            scanned=scanned,
            reencrypted=reencrypted,
            status=await self.keypair_secret_status(),
        )

    async def keypair_secret_status(self) -> SecretSweepStatus:
        """Count the stored secrets by the provider and key holding them."""
        holders: Counter[tuple[KeyProviderType, SecretKeyId | None]] = Counter()
        cursor: AccessKey | None = None
        async with self._ops.read_ops() as r:
            while True:
                stored = await r.scan_keypair_secrets(cursor, _CHUNK_SIZE)
                for secret in stored:
                    holders[self._key_provider_pool.holder_of(secret.value)] += 1
                    cursor = secret.access_key
                if len(stored) < _CHUNK_SIZE:
                    break
        return SecretSweepStatus(
            write_provider_type=self._key_provider_pool.write_provider_type(),
            counts=self._to_counts(holders),
        )

    def _to_counts(
        self, holders: Counter[tuple[KeyProviderType, SecretKeyId | None]]
    ) -> Sequence[SecretKeyIdCount]:
        return [
            SecretKeyIdCount(provider_type=provider_type, key_id=key_id, count=count)
            for (provider_type, key_id), count in sorted(
                holders.items(), key=lambda item: (item[0][0], item[0][1] or "")
            )
        ]
