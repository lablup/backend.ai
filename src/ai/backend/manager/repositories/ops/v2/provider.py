"""V2 DB ops provider.

Executes the v2 write specs (``models/specs/``): the spec declares what to write —
row, membership, checks — and this layer performs it. Self-contained on purpose —
nothing here inherits from the legacy provider, and only the data-returning read
paths exist, so a domain handed this provider cannot reach any legacy path and
removing the legacy provider later touches nothing here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2DBOpsProvider:
    """Hands out session-bound ops over the v2 specs; the engine stays private."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @asynccontextmanager
    async def read_ops(self) -> AsyncGenerator[V2ReadOps]:
        """Open a read-only transaction and yield read-only ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield V2ReadOps(sess)

    @asynccontextmanager
    async def write_ops(self) -> AsyncGenerator[V2WriteOps]:
        """Open a read-write transaction and yield the v2 write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2WriteOps(sess)
