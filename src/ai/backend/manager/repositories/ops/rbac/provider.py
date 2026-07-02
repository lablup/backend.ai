"""RBAC-scoped DB ops: scope-associated entity creation on top of the base ops."""

from __future__ import annotations

from collections.abc import AsyncIterator, Collection, Sequence
from contextlib import asynccontextmanager
from typing import override

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RelationType
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreatorResult,
    RBACEntityCreator,
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation."""

    _role_manager: RoleManager

    def __init__(self, sess: SASession) -> None:
        super().__init__(sess)
        self._role_manager = RoleManager()

    async def bulk_create_scoped[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResult[TRow]:
        """Insert rows with their RBAC scope associations (each creator carries its scope)."""
        return await execute_rbac_entity_creators(self._sess, creators)

    async def add_users_to_scope(
        self,
        scope_id: ScopeId,
        user_ids: Collection[UserID],
    ) -> None:
        """Bind users to a scope and grant the scope's ``auto_assign`` roles.

        Inserts the user-scope associations (``association_scopes_entities``,
        ON CONFLICT DO NOTHING) and maps every user to each active
        ``auto_assign`` role bound to the scope. Idempotent: re-binding an
        existing membership is a no-op and already-granted roles are skipped,
        so it is safe to call even when the scope association already exists.
        """
        if not user_ids:
            return
        values = [
            {
                "scope_type": scope_id.scope_type,
                "scope_id": scope_id.scope_id,
                "entity_type": EntityType.USER,
                "entity_id": str(user_id),
                "relation_type": RelationType.AUTO,
                "permission_cap": None,
            }
            for user_id in user_ids
        ]
        stmt = pg_insert(AssociationScopesEntitiesRow).values(values).on_conflict_do_nothing()
        await self._sess.execute(stmt)
        await self._role_manager.assign_auto_assign_roles(self._sess, user_ids, scope_id)


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
