"""Retention DB ops provider.

Hands out :class:`RetentionWriteOps` where :class:`V2DBOpsProvider` hands out the
general write ops, so the drain primitive reaches a repository by injection rather
than by every repository inheriting it.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.retention.write import RetentionWriteOps


class RetentionOpsProvider(V2DBOpsProvider):
    """Hands out :class:`RetentionWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[RetentionWriteOps]:
        """Open a read-write transaction and yield the retention write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield RetentionWriteOps(sess)
