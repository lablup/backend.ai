"""Secret sweep DB ops provider.

Hands out the sweep ops where :class:`V2DBOpsProvider` hands out the general ones,
so the scan and the conditional rewrite reach a repository by injection rather than
by every repository inheriting them.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.secret.read import SecretReadOps
from ai.backend.manager.repositories.ops.v2.secret.write import SecretWriteOps


class SecretOpsProvider(V2DBOpsProvider):
    """Hands out the secret sweep ops on both surfaces."""

    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[SecretReadOps]:
        """Open a read-only transaction and yield the secret sweep read ops."""
        async with self._db.begin_readonly_session_read_committed() as sess:
            yield SecretReadOps(sess)

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[SecretWriteOps]:
        """Open a read-write transaction and yield the secret sweep write ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield SecretWriteOps(sess)
