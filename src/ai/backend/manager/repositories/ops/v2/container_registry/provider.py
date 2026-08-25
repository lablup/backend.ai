"""Container registry DB ops provider.

Hands out :class:`ContainerRegistryWriteOps` where :class:`V2DBOpsProvider` hands out
the general write ops, so the registry-project edges reach a repository by injection.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.container_registry.write import (
    ContainerRegistryWriteOps,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class ContainerRegistryOpsProvider(V2DBOpsProvider):
    """Hands out :class:`ContainerRegistryWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[ContainerRegistryWriteOps]:
        """Open a read-write transaction and yield the container registry write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield ContainerRegistryWriteOps(sess)
