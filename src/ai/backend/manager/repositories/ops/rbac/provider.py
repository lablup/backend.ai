"""RBAC-scoped DB ops: scope-associated entity creation and virtual-entity ownership
on top of the base write ops."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Collection, Sequence
from contextlib import asynccontextmanager
from typing import override

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import ScopeRef, ScopeType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import (
    BulkCreator,
    CreatorSpec,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.creators import (
    UserRoleCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation and virtual-entity writes."""

    async def _bulk_create_ignore_conflicts[TRow: Base](
        self, specs: Sequence[CreatorSpec[TRow]]
    ) -> None:
        """Insert rows from ``specs`` in one statement, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(self._sess, [spec.build_row() for spec in specs])

    async def _bulk_create_dependent_ignore_conflicts[TDependency, TRow: Base](
        self,
        specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
        dependency: TDependency,
    ) -> None:
        """Insert dependency-resolved rows from ``specs``, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(
            self._sess, [spec.build_row(dependency) for spec in specs]
        )

    # -- Virtual-entity helpers ----------------------------------------------------

    async def _find_virtual_entity_id(self, scope: ScopeRef) -> VirtualEntityID | None:
        """Return the virtual entity id backing ``scope``, or ``None`` if it has none."""
        stmt = sa.select(VirtualEntityRow.id).where(
            VirtualEntityRow.entity_type == scope.scope_type,
            VirtualEntityRow.entity_id == scope.scope_id,
        )
        return (await self._sess.execute(stmt)).scalar_one_or_none()

    async def _resolve_virtual_entity_id(self, scope: ScopeRef) -> VirtualEntityID:
        """Return the virtual entity id backing ``scope``.

        Every owner scope is created with its virtual entity, so a missing one is an
        invariant violation: raises :class:`VirtualEntityNotFound` (500).
        """
        virtual_entity_id = await self._find_virtual_entity_id(scope)
        if virtual_entity_id is None:
            raise VirtualEntityNotFound(
                f"No virtual entity for scope {scope.scope_type}:{scope.scope_id}"
            )
        return virtual_entity_id

    async def _find_virtual_entity_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualEntityID]:
        """Return the virtual entity ids backing ``scopes`` in one query; scopes
        without one are absent from the result."""
        if not scopes:
            return {}
        stmt = sa.select(
            VirtualEntityRow.entity_type,
            VirtualEntityRow.entity_id,
            VirtualEntityRow.id,
        ).where(
            sa.tuple_(VirtualEntityRow.entity_type, VirtualEntityRow.entity_id).in_([
                (s.scope_type, s.scope_id) for s in scopes
            ])
        )
        return {
            ScopeRef(scope_type=ScopeType(row.entity_type), scope_id=row.entity_id): row.id
            for row in (await self._sess.execute(stmt)).all()
        }

    async def _resolve_virtual_entity_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualEntityID]:
        """Return the virtual entity id backing each of ``scopes`` in one query.

        As with :meth:`_resolve_virtual_entity_id`, a scope without a virtual entity is
        an invariant violation: raises :class:`VirtualEntityNotFound` naming them all.
        """
        resolved = await self._find_virtual_entity_ids(scopes)
        missing = [s for s in scopes if s not in resolved]
        if missing:
            raise VirtualEntityNotFound(
                "No virtual entity for scopes: "
                + ", ".join(f"{s.scope_type}:{s.scope_id}" for s in missing)
            )
        return resolved

    async def _insert_virtual_entities(self, scopes: Sequence[ScopeRef]) -> None:
        """Create each scope's virtual entity node with its self entity-membership and self
        scope_binding (permission_cap NULL). Idempotent: an existing scope is a no-op."""
        if not scopes:
            return
        values = [{"entity_type": s.scope_type, "entity_id": s.scope_id} for s in scopes]
        insert_stmt = (
            pg_insert(VirtualEntityRow)
            .values(values)
            .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
            .returning(
                VirtualEntityRow.id,
                VirtualEntityRow.entity_type,
                VirtualEntityRow.entity_id,
            )
        )
        inserted = (await self._sess.execute(insert_stmt)).all()
        if not inserted:
            return
        membership_stmt = (
            pg_insert(EntityMembershipRow)
            .values([
                {
                    "virtual_entity_id": row.id,
                    "member_entity_id": row.id,
                    "capped": False,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(membership_stmt)
        binding_stmt = (
            pg_insert(ScopeBindingRow)
            .values([
                {
                    "virtual_entity_id": row.id,
                    "scope_entity_id": row.id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(binding_stmt)

    async def _grant_auto_assign_roles(
        self,
        scope_id: ScopeId,
        user_ids: Collection[UserID],
    ) -> None:
        """Map users to every active ``auto_assign`` role bound to ``scope_id``.

        Roles bound to the scope are located via the scope-entity association
        (``association_scopes_entities`` with ``entity_type == ROLE``); already-granted
        pairs are skipped.
        """
        unique_user_ids = set(user_ids)
        if not unique_user_ids:
            return
        # One query: the scope's auto_assign roles, outer-joined with the target
        # users' existing grants (user_id is NULL for roles no target user holds).
        rows = (
            await self._sess.execute(
                sa.select(RoleRow.id.label("role_id"), UserRoleRow.user_id.label("user_id"))
                .join(
                    AssociationScopesEntitiesRow,
                    sa.cast(AssociationScopesEntitiesRow.entity_id, sa.String)
                    == sa.cast(RoleRow.id, sa.String),
                )
                .outerjoin(
                    UserRoleRow,
                    sa.and_(
                        UserRoleRow.role_id == RoleRow.id,
                        UserRoleRow.user_id.in_(unique_user_ids),
                    ),
                )
                .where(
                    AssociationScopesEntitiesRow.scope_type == scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == LegacyEntityType.ROLE,
                    RoleRow.auto_assign.is_(True),
                    RoleRow.status == RoleStatus.ACTIVE,
                )
            )
        ).all()
        role_ids = {row.role_id for row in rows}
        existing_pairs = {(row.user_id, row.role_id) for row in rows if row.user_id is not None}
        specs = [
            UserRoleCreatorSpec(user_id=user_id, role_id=role_id)
            for user_id in unique_user_ids
            for role_id in role_ids
            if (user_id, role_id) not in existing_pairs
        ]
        if specs:
            await self.bulk_create(BulkCreator(specs=specs))

    # -- Virtual entity: ensure compatibility for externally-created rows ----------

    async def ensure_scope(self, scope: ScopeRef) -> None:
        """Ensure the virtual entity node for an already-created ``scope``. Idempotent."""
        await self._insert_virtual_entities([scope])


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)
