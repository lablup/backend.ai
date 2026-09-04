"""Permission DB ops provider.

Hands out the permission ops where :class:`V2DBOpsProvider` hands out the general
ones, so the role permission writes reach a repository by injection rather than by
every repository inheriting them.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.permission.read import PermissionReadOps
from ai.backend.manager.repositories.ops.v2.permission.write import PermissionWriteOps
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class PermissionOpsProvider(V2DBOpsProvider):
    """Hands out the permission ops on both surfaces."""

    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[PermissionReadOps]:
        """Open a read-only transaction and yield the permission read ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield PermissionReadOps(sess)

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[PermissionWriteOps]:
        """Open a read-write transaction and yield the permission write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield PermissionWriteOps(sess)
