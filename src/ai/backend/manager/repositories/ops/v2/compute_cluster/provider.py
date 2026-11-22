"""Compute cluster DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.compute_cluster.write import (
    V2ComputeClusterWriteOps,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ComputeClusterOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2ComputeClusterWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2ComputeClusterWriteOps]:
        """Open a read-write transaction and yield the compute cluster write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2ComputeClusterWriteOps(sess)
