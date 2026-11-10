"""Relation DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.write import V2RelationWriteOps


class RelationOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2RelationWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2RelationWriteOps]:
        """Open a read-write transaction and yield the relation write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2RelationWriteOps(sess)
