"""Binder for RBAC scope association bind/unbind operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)

# =============================================================================
# Binder Dataclass
# =============================================================================


@dataclass
class RBACScopeBinder:
    """Binder for updating scope associations of an existing RBAC entity.

    Handles N:N scope mapping changes by inserting new associations (bind)
    and deleting removed associations (unbind) in a single operation.

    Attributes:
        element_type: The RBAC element type of the target entity.
        entity_id: The primary key (as string) of the target entity.
        bind_scope_refs: Scope references to associate with the entity.
        unbind_scope_refs: Scope references to disassociate from the entity.
        relation_type: The relation type for newly bound associations. Defaults to AUTO.
    """

    element_type: RBACElementType
    entity_id: str
    bind_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    unbind_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    relation_type: RelationType = RelationType.AUTO


@dataclass
class RBACScopeBinderResult:
    """Result of executing a scope binder operation."""

    bound_count: int
    unbound_count: int


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_scope_binder(
    db_sess: SASession,
    binder: RBACScopeBinder,
) -> RBACScopeBinderResult:
    """Execute scope bind/unbind operations for an RBAC entity.

    Operations:
    1. Delete associations for unbind_scope_refs (if any)
    2. Insert associations for bind_scope_refs (if any), using ON CONFLICT DO NOTHING

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        binder: Binder instance specifying which scopes to bind/unbind.

    Returns:
        RBACScopeBinderResult with counts of bound and unbound associations.
    """
    entity_type = binder.element_type.to_entity_type()
    unbound_count = 0
    bound_count = 0

    # 1. Unbind: delete associations for removed scopes
    if binder.unbind_scope_refs:
        unbind_conditions = [
            sa.and_(
                AssociationScopesEntitiesRow.scope_type == ref.element_type.to_scope_type(),
                AssociationScopesEntitiesRow.scope_id == ref.element_id,
            )
            for ref in binder.unbind_scope_refs
        ]
        result = await db_sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == entity_type,
                    AssociationScopesEntitiesRow.entity_id == binder.entity_id,
                    sa.or_(*unbind_conditions),
                )
            )
        )
        unbound_count = cast(CursorResult[Any], result).rowcount or 0

    # 2. Bind: insert associations for new scopes (ON CONFLICT DO NOTHING)
    if binder.bind_scope_refs:
        values_list = [
            {
                "scope_type": ref.element_type.to_scope_type(),
                "scope_id": ref.element_id,
                "entity_type": entity_type,
                "entity_id": binder.entity_id,
                "relation_type": binder.relation_type,
            }
            for ref in binder.bind_scope_refs
        ]
        stmt = (
            pg_insert(AssociationScopesEntitiesRow)
            .values(values_list)
            .on_conflict_do_nothing(
                constraint="uq_scope_id_entity_id",
            )
        )
        result = await db_sess.execute(stmt)
        bound_count = cast(CursorResult[Any], result).rowcount or 0

    return RBACScopeBinderResult(
        bound_count=bound_count,
        unbound_count=unbound_count,
    )
