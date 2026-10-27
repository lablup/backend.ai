"""Resource allocation DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_allocation.read import (
    ResourceAllocationReadOps,
)


class ResourceAllocationOpsProvider(V2DBOpsProvider):
    """Hands out :class:`ResourceAllocationReadOps` for the read-only surface."""

    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[ResourceAllocationReadOps]:
        """Open a read-only transaction and yield the resource allocation read ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield ResourceAllocationReadOps(sess)
