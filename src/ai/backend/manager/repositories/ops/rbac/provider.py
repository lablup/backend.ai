"""RBAC-scoped DB ops: scope-associated entity creation on top of the base ops."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreatorResult,
    RBACEntityCreator,
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation."""

    async def bulk_create_scoped[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResult[TRow]:
        """Insert rows with their RBAC scope associations (each creator carries its scope)."""
        return await execute_rbac_entity_creators(self._sess, creators)


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
