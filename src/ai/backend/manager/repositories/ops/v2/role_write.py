"""Role writes of the v2 ops: which roles a user holds.

Holding a role is what activates its permissions, so this is not a graph edge and not a
relation the business layer reads — it is the mapping the permission layer resolves
through. The primitives stand on their own: a member's roles change without the
membership changing, and joining an organization grants roles as its second step
(`proposals/BEP-1076-project-membership.md`).
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import ClassVar

import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2RoleWriteOps(V2WriteOpsBase):
    """Grants and revocations of the roles a user holds, bound to a single session."""

    _ROLE_ENTITY_TYPE: ClassVar[EntityType] = EntityType("role")

    async def grant_roles(
        self,
        user_id: UserID,
        role_ids: Collection[RoleID],
        granted_by: UserID | None = None,
    ) -> None:
        """Give the user every named role, skipping the ones already held.

        Idempotent on the (user, role) pair: granting twice leaves the first grant's
        ``granted_by`` and ``granted_at`` alone, since the first is when it started.
        """
        if not role_ids:
            return
        await self._bulk_insert_ignore_conflicts([
            UserRoleRow(user_id=user_id, role_id=role_id, granted_by=granted_by)
            for role_id in role_ids
        ])

    async def revoke_roles(self, user_id: UserID, role_ids: Collection[RoleID]) -> None:
        """Take the named roles back from the user.

        Silent on what was never held — a revocation states the absence it leaves.
        """
        if not role_ids:
            return
        await self._sess.execute(
            sa.delete(UserRoleRow).where(
                UserRoleRow.user_id == user_id,
                UserRoleRow.role_id.in_(list(role_ids)),
            )
        )

    async def role_ids_enrolled_in(self, scope: EntityIdentifier) -> Sequence[RoleID]:
        """Every active role enrolled in the scope's virtual scope.

        What a membership's roles are drawn from, and what leaving takes back: a role
        enrolled in a scope is not one a non-member holds.
        """
        return await self._enrolled_role_ids(scope, auto_assign_only=False)

    async def auto_assign_role_ids_in(self, scope: EntityIdentifier) -> Sequence[RoleID]:
        """The scope's roles that a joining member receives when none was named."""
        return await self._enrolled_role_ids(scope, auto_assign_only=True)

    async def _enrolled_role_ids(
        self, scope: EntityIdentifier, *, auto_assign_only: bool
    ) -> Sequence[RoleID]:
        stmt = (
            sa.select(RoleRow.id)
            .join(EntityMembershipRow, EntityMembershipRow.entity_id == RoleRow.id)
            .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == scope.entity_type(),
                VirtualScopeRow.scope_id == scope,
                EntityMembershipRow.entity_type == self._ROLE_ENTITY_TYPE,
                RoleRow.status == RoleStatus.ACTIVE,
            )
        )
        if auto_assign_only:
            stmt = stmt.where(RoleRow.auto_assign.is_(True))
        return [RoleID(row) for row in (await self._sess.scalars(stmt)).all()]
