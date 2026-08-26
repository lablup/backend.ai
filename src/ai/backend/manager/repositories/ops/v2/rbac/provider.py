"""RBAC DB ops provider.

Hands out :class:`V2RBACWriteOps` where :class:`V2DBOpsProvider` hands out the general
write ops, so the role primitives reach a repository by injection rather than by sitting
on every domain's ops.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.rbac.write import V2RBACWriteOps


class V2RBACOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2RBACWriteOps]:
        """Open a read-write transaction and yield the RBAC write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2RBACWriteOps(sess)
