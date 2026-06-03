"""Composite spec for race-free scope teardown.

Mirror of :mod:`scope_creator`. ``ScopePurger`` extends the generic :class:`Purger`
(its inherited ``row_class`` / ``pk_value`` identify the scope row to delete) and
adds the scope's :class:`ScopeContext`. :func:`execute_scope_purger` runs the
inverse sequence: drop scope-bound permission rows, drop the scope's association
rows, and finally drop the scope row itself.

Roles are intentionally left alone — role lifecycle is independent of scope
lifecycle, and a role may be reused or reassigned after a scope is gone.

The permission and association rows are deleted generically from the scope's
:class:`ScopeContext`: they are written uniformly at provisioning time
(``scope_type`` / ``scope_id`` on permissions; the scope referenced as scope or
as entity on associations), so the inverse filter needs no per-scope-type spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

from .purger import BatchPurger, BatchPurgerSpec, Purger, execute_batch_purger, execute_purger
from .types import ScopeContext

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


@dataclass
class ScopePurger[TScopeRow: Base](Purger[TScopeRow]):
    """Bundles a scope teardown for :func:`execute_scope_purger`.

    Extends :class:`Purger`: the inherited ``row_class`` / ``pk_value`` identify the
    scope row to delete, so the row delete is delegated to ``execute_purger``
    directly. ``scope_context`` locates the scope-bound RBAC rows to purge first.
    """

    scope_context: ScopeContext


@dataclass
class ScopePurgerResult[TScopeRow: Base]:
    """Outcome of a scope teardown."""

    scope_row: TScopeRow | None
    deleted_permission_count: int
    deleted_association_count: int


@dataclass(frozen=True)
class _ScopePermissionsPurgeSpec(BatchPurgerSpec[PermissionRow]):
    """Select every permission row pinned to a scope, derived from its context.

    Mirrors how :func:`execute_scope_creator` stamps ``scope_type`` / ``scope_id``
    onto each permission at provisioning time.
    """

    scope_context: ScopeContext

    def build_subquery(self) -> sa.sql.Select[tuple[PermissionRow]]:
        return sa.select(PermissionRow).where(
            PermissionRow.scope_type == self.scope_context.scope_type.to_scope_type(),
            PermissionRow.scope_id == self.scope_context.scope_id,
        )


@dataclass(frozen=True)
class _ScopeAssociationsPurgeSpec(BatchPurgerSpec[AssociationScopesEntitiesRow]):
    """Select every association row that references a scope, as scope or as entity.

    Role-to-scope rows reference the scope as the scope side; parent-scope rows
    (e.g. a project under its domain) reference it as the entity side. Both are
    OR-combined so a single batched delete drops the whole set.
    """

    scope_context: ScopeContext

    def build_subquery(self) -> sa.sql.Select[tuple[AssociationScopesEntitiesRow]]:
        scope_type = self.scope_context.scope_type
        scope_id = self.scope_context.scope_id
        return sa.select(AssociationScopesEntitiesRow).where(
            sa.or_(
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == scope_type.to_scope_type(),
                    AssociationScopesEntitiesRow.scope_id == scope_id,
                ),
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == scope_type.to_entity_type(),
                    AssociationScopesEntitiesRow.entity_id == scope_id,
                ),
            )
        )


async def execute_scope_purger[TScopeRow: Base](
    db_sess: SASession,
    scope_purger: ScopePurger[TScopeRow],
) -> ScopePurgerResult[TScopeRow]:
    """Tear down a scope and the scope-bound RBAC rows it leaves behind.

    Order: scope-pinned permission rows, then association rows, then the scope row
    itself. Roles are not touched — role lifecycle is independent of scope
    lifecycle. The scope row delete is delegated to ``execute_purger``
    (``ScopePurger`` is a ``Purger``); the RBAC rows reuse ``execute_batch_purger``.

    The caller controls the transaction boundary (commit/rollback).
    """
    scope_context = scope_purger.scope_context

    perm_res = await execute_batch_purger(
        db_sess,
        BatchPurger(spec=_ScopePermissionsPurgeSpec(scope_context=scope_context)),
    )
    assoc_res = await execute_batch_purger(
        db_sess,
        BatchPurger(spec=_ScopeAssociationsPurgeSpec(scope_context=scope_context)),
    )
    scope_res = await execute_purger(db_sess, scope_purger)

    return ScopePurgerResult(
        scope_row=scope_res.row if scope_res is not None else None,
        deleted_permission_count=perm_res.deleted_count,
        deleted_association_count=assoc_res.deleted_count,
    )
