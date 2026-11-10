"""Storage status DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.storage_status.write import V2StorageStatusWriteOps


class StorageStatusOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2StorageStatusWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2StorageStatusWriteOps]:
        """Open a read-write transaction and yield the storage status write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2StorageStatusWriteOps(sess)
