"""User provisioning DB ops provider."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import V2UserWriteOps


class UserOpsProvider(V2DBOpsProvider):
    """Hands out :class:`V2UserWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[V2UserWriteOps]:
        """Open a read-write transaction and yield the user provisioning ops."""
        async with self._db.begin_session_read_committed() as sess:
            yield V2UserWriteOps(sess)
