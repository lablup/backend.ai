"""Database source for the stored-secret re-encryption pass.

Walks every encrypted column named in :meth:`SecretDBSource._targets`, chunk by chunk,
and encrypts each value again through the write provider under a fresh data encryption
key. Every row is treated alike, whatever key it was on: a pass interrupted halfway is
resumed by running it again.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from typing import Any, Final

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.secret.types import (
    KeyProviderType,
    SecretKeyCount,
    SecretKeyId,
    SecretReencryptProgress,
    SecretStatus,
)
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.ops.v2.secret.read import SecretTarget
from ai.backend.manager.secret.pool import KeyProviderPool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Rows one chunk reads and writes back in a single transaction, so a large table never
# becomes one long-held transaction.
_CHUNK_SIZE: Final[int] = 1000

# Every column stored through a secret column. A column joins the pass by being listed
# here, and its own type supplies the associated data it is read under.
_TARGETS: Final[tuple[SecretTarget, ...]] = (
    SecretTarget(row_class=KeyPairRow, key_column="access_key", secret_column="secret_key"),
)


class SecretDBSource:
    _ops: SecretOpsProvider
    _key_provider_pool: KeyProviderPool

    def __init__(self, ops_provider: SecretOpsProvider, key_provider_pool: KeyProviderPool) -> None:
        self._ops = ops_provider
        self._key_provider_pool = key_provider_pool

    def _targets(self) -> Sequence[SecretTarget]:
        return _TARGETS

    async def reencrypt(self) -> SecretReencryptProgress:
        """Encrypt every stored secret again through the write provider.

        Each chunk reads its rows and writes them back in the same transaction, and every
        write carries the value it read as its condition, so a secret rewritten mid-pass
        keeps its new value.
        """
        scanned = 0
        reencrypted = 0
        for target in self._targets():
            column_scanned, column_reencrypted = await self._reencrypt_column(target)
            scanned += column_scanned
            reencrypted += column_reencrypted
        log.info("secret re-encryption read {} secret(s) and wrote {}", scanned, reencrypted)
        return SecretReencryptProgress(
            scanned=scanned,
            reencrypted=reencrypted,
            status=await self.status(),
        )

    async def _reencrypt_column(self, target: SecretTarget) -> tuple[int, int]:
        context = target.context()
        cursor: Any | None = None
        scanned = 0
        reencrypted = 0
        while True:
            async with self._ops.write_ops() as w:
                stored = await w.scan_secrets(target, cursor, _CHUNK_SIZE)
                for secret in stored:
                    scanned += 1
                    cursor = secret.key
                    replacement = await self._key_provider_pool.reencrypt(secret.value, context)
                    if await w.rewrite_secret(target, secret.key, secret.value, replacement):
                        reencrypted += 1
            if len(stored) < _CHUNK_SIZE:
                return scanned, reencrypted

    async def status(self) -> SecretStatus:
        """Count every column's stored secrets by the provider and key holding them."""
        counts: list[SecretKeyCount] = []
        for target in self._targets():
            counts.extend(await self._count_column(target))
        return SecretStatus(
            write_provider_type=self._key_provider_pool.write_provider_type(),
            counts=counts,
        )

    async def _count_column(self, target: SecretTarget) -> Sequence[SecretKeyCount]:
        holders: Counter[tuple[KeyProviderType, SecretKeyId | None]] = Counter()
        cursor: Any | None = None
        async with self._ops.read_ops() as r:
            while True:
                stored = await r.scan_secrets(target, cursor, _CHUNK_SIZE)
                for secret in stored:
                    holders[self._key_provider_pool.holder_of(secret.value)] += 1
                    cursor = secret.key
                if len(stored) < _CHUNK_SIZE:
                    break
        column = target.context()
        return [
            SecretKeyCount(column=column, provider_type=provider_type, key_id=key_id, count=count)
            for (provider_type, key_id), count in sorted(
                holders.items(), key=lambda item: (item[0][0], item[0][1] or "")
            )
        ]
