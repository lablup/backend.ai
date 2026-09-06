"""User provisioning DB ops provider.

Hands out the user provisioning ops where :class:`RBACOpsProvider` hands out the RBAC
ones, so full user creation reaches a repository by injection rather than by every
repository inheriting it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.manager.repositories.ops.user.write import UserWriteOps


class UserOpsProvider(RBACOpsProvider):
    """Hands out :class:`UserWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[UserWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield UserWriteOps(sess)
