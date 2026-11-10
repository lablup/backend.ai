"""Share DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.write import V2ShareWriteOps


class ShareOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2ShareWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2ShareWriteOps]:
        """Open a read-write transaction and yield the share write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2ShareWriteOps(sess)
