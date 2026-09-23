"""Domain provisioning DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.domain.write import V2DomainWriteOps
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class DomainOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2DomainWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2DomainWriteOps]:
        """Open a read-write transaction and yield the domain provisioning ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2DomainWriteOps(sess)
