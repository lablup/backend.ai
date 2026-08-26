"""Writes of the RBAC concern: links between entities, and the roles a user holds.

Both answer the same kind of question — who may put these two things together — and
putting a user in an organization writes a link and grants a role in one transaction, so
they are one set of primitives rather than two.

A link is generic: a spec says which table and which columns, so any domain's relation is
written through here. Holding a role is not a graph edge and not a relation the business
layer reads; it is the mapping the permission layer resolves through.

One concern holds these, so they extend the general write ops rather than joining them,
and reach a repository by injecting :class:`V2RBACOpsProvider`.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md` and BEP-1076.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import ClassVar

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2RBACWriteOps(V2WriteOps):
    """Links and role grants of the RBAC concern, bound to a single session."""

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

    async def create_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        creator: RelationCreator[TRow],
    ) -> bool:
        """Link the two entities, answering whether this call is what linked them.

        A pair that is already taken is settled by the spec: left alone, or written over
        to revive a relation that was switched off.
        """
        row = creator.build_row(left, right)
        row_class = creator.row_class()
        table = row_class.__table__
        column_keys = {c.key for c in sa.inspect(row_class).columns}
        values = {k: v for k, v in row.__dict__.items() if k in column_keys}
        stmt = pg_insert(table).values(values)
        conflict_values = creator.build_conflict_values()
        if conflict_values is None:
            stmt = stmt.on_conflict_do_nothing(index_elements=creator.index_elements())
        else:
            stmt = stmt.on_conflict_do_update(
                index_elements=creator.index_elements(), set_=conflict_values
            )
        try:
            result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(
                self._parse_integrity_error(e), creator.integrity_error_checks()
            )
        await self._sess.flush()
        return result.first() is not None

    async def delete_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        """Switch the relation off, answering whether a row was there to switch."""
        return await self._write_relation_lifecycle(left, right, updater)

    async def restore_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        """Switch the relation back on, answering whether a row was there to switch.

        The reverse of :meth:`delete_relation` and a separate method for the same reason
        the entity soft delete and restore are: the operation an action declares is what
        RBAC checks and what the audit row records, and the two must not be one call
        that takes the direction as a value.
        """
        return await self._write_relation_lifecycle(left, right, updater)

    async def purge_relation[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        purger: RelationPurger[TRow],
    ) -> bool:
        """Remove the row linking the two entities, answering whether one went."""
        await self._validate_conflict_checks(purger.conflict_checks())
        row_class = purger.row_class()
        table = row_class.__table__
        stmt = sa.delete(table).where(self._relation_clause(purger.conditions(left, right)))
        result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        await self._sess.flush()
        return result.first() is not None

    async def _write_relation_lifecycle[TRow: Base](
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[TRow],
    ) -> bool:
        table = updater.row_class().__table__
        stmt = (
            sa.update(table)
            .values(updater.build_values())
            .where(self._relation_clause(updater.conditions(left, right)))
        )
        result = await self._sess.execute(stmt.returning(*table.primary_key.columns))
        await self._sess.flush()
        return result.first() is not None

    def _relation_clause(
        self, conditions: Sequence[QueryCondition]
    ) -> sa.sql.expression.ColumnElement[bool]:
        """AND the spec's conditions; an empty declaration would name every row, so it
        is refused rather than executed."""
        if not conditions:
            raise ValueError("a relation spec must name the pair with at least one condition")
        return sa.and_(*[condition() for condition in conditions])
