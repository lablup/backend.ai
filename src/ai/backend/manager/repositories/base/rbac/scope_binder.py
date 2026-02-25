"""Binder/Unbinder for RBAC scope association operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)

# =============================================================================
# Binder
# =============================================================================


@dataclass
class RBACScopeBinder:
    """Binds new scope associations to an existing RBAC entity.

    Inserts AssociationScopesEntitiesRows for each scope reference,
    using ON CONFLICT DO NOTHING for idempotency.

    Attributes:
        element_type: The RBAC element type of the target entity.
        entity_id: The primary key (as string) of the target entity.
        scope_refs: Scope references to associate with the entity.
        relation_type: The relation type for the new associations. Defaults to AUTO.
    """

    element_type: RBACElementType
    entity_id: str
    scope_refs: Sequence[RBACElementRef]
    relation_type: RelationType = RelationType.AUTO


@dataclass
class RBACScopeBinderResult:
    """Result of executing a scope binder operation."""

    rows: list[AssociationScopesEntitiesRow]


async def execute_rbac_scope_binder(
    db_sess: SASession,
    binder: RBACScopeBinder,
) -> RBACScopeBinderResult:
    """Insert scope associations for an RBAC entity.

    Uses INSERT ... ON CONFLICT DO NOTHING with RETURNING to retrieve
    only the newly inserted rows.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        binder: Binder instance specifying which scopes to bind.

    Returns:
        RBACScopeBinderResult with the newly inserted AssociationScopesEntitiesRows.
    """
    if not binder.scope_refs:
        return RBACScopeBinderResult(rows=[])

    entity_type = binder.element_type.to_entity_type()

    values_list = [
        {
            "scope_type": ref.element_type.to_scope_type(),
            "scope_id": ref.element_id,
            "entity_type": entity_type,
            "entity_id": binder.entity_id,
            "relation_type": binder.relation_type,
        }
        for ref in binder.scope_refs
    ]
    stmt = (
        pg_insert(AssociationScopesEntitiesRow)
        .values(values_list)
        .on_conflict_do_nothing(constraint="uq_scope_id_entity_id")
        .returning(AssociationScopesEntitiesRow)
    )
    rows = list((await db_sess.scalars(stmt)).all())

    return RBACScopeBinderResult(rows=rows)


# =============================================================================
# Unbinder
# =============================================================================


@dataclass
class RBACScopeUnbinder:
    """Unbinds scope associations from an existing RBAC entity.

    Deletes AssociationScopesEntitiesRows matching the given scope references.

    Attributes:
        element_type: The RBAC element type of the target entity.
        entity_id: The primary key (as string) of the target entity.
        scope_refs: Scope references to disassociate from the entity.
    """

    element_type: RBACElementType
    entity_id: str
    scope_refs: Sequence[RBACElementRef]


@dataclass
class RBACScopeUnbinderResult:
    """Result of executing a scope unbinder operation."""

    rows: list[AssociationScopesEntitiesRow]


async def execute_rbac_scope_unbinder(
    db_sess: SASession,
    unbinder: RBACScopeUnbinder,
) -> RBACScopeUnbinderResult:
    """Delete scope associations for an RBAC entity.

    Uses DELETE ... RETURNING to retrieve the deleted rows.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Unbinder instance specifying which scopes to unbind.

    Returns:
        RBACScopeUnbinderResult with the deleted AssociationScopesEntitiesRows.
    """
    if not unbinder.scope_refs:
        return RBACScopeUnbinderResult(rows=[])

    entity_type = unbinder.element_type.to_entity_type()

    scope_conditions = [
        sa.and_(
            AssociationScopesEntitiesRow.scope_type == ref.element_type.to_scope_type(),
            AssociationScopesEntitiesRow.scope_id == ref.element_id,
        )
        for ref in unbinder.scope_refs
    ]
    stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(
            sa.and_(
                AssociationScopesEntitiesRow.entity_type == entity_type,
                AssociationScopesEntitiesRow.entity_id == unbinder.entity_id,
                sa.or_(*scope_conditions),
            )
        )
        .returning(AssociationScopesEntitiesRow)
    )
    rows = list((await db_sess.scalars(stmt)).all())

    return RBACScopeUnbinderResult(rows=rows)
