"""Binder/Unbinder for RBAC scope association operations.

Bundles both N:N mapping row writes and RBAC association writes
into single types, analogous to how RBACEntityCreator bundles
entity row creation with RBAC association writes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    CreatorSpec,
    execute_bulk_creator,
)
from ai.backend.manager.repositories.base.purger import (
    BatchPurger,
    BatchPurgerSpec,
    execute_batch_purger,
)

# =============================================================================
# Binder Pair
# =============================================================================


@dataclass(frozen=True)
class RBACScopeBindingPair[TRow: Base]:
    """A paired business row spec + RBAC binding for scope association.

    Bundles a CreatorSpec (for the N:N mapping row) with RBAC element
    references (for the association_scopes_entities row) so that each
    business row is always paired with its RBAC association.

    Attributes:
        spec: CreatorSpec for the N:N mapping row to insert.
        entity_ref: RBAC element reference for the entity (e.g., RESOURCE_GROUP, "sg1").
        scope_ref: RBAC element reference for the scope (e.g., DOMAIN, "d1").
        relation_type: Edge type for this particular binding. Defaults to AUTO.
    """

    spec: CreatorSpec[TRow]
    entity_ref: RBACElementRef
    scope_ref: RBACElementRef
    relation_type: RelationType = RelationType.AUTO


# =============================================================================
# Binder
# =============================================================================


@dataclass
class RBACScopeBinder[TRow: Base]:
    """Binds N:N mapping rows and RBAC scope associations atomically.

    Combines business row creation (e.g., sgroups_for_domains)
    with RBAC association writes (association_scopes_entities).

    Attributes:
        pairs: Paired business row specs and RBAC bindings.
    """

    pairs: Sequence[RBACScopeBindingPair[TRow]]


@dataclass
class RBACScopeBinderResult[TRow: Base]:
    """Result of executing a scope binder operation.

    Attributes:
        rows: Business N:N mapping rows created.
        association_rows: RBAC association rows created (newly inserted only).
    """

    rows: list[TRow]
    association_rows: list[AssociationScopesEntitiesRow]


async def execute_rbac_scope_binder[TRow: Base](
    db_sess: SASession,
    binder: RBACScopeBinder[TRow],
) -> RBACScopeBinderResult[TRow]:
    """Insert N:N mapping rows and RBAC scope associations.

    Operations:
    1. Bulk-create business rows from paired specs
    2. INSERT AssociationScopesEntitiesRow for each pair
       (ON CONFLICT DO NOTHING + RETURNING)

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        binder: Binder instance specifying paired rows and bindings.

    Returns:
        RBACScopeBinderResult with created business rows and RBAC associations.
    """
    if not binder.pairs:
        return RBACScopeBinderResult(rows=[], association_rows=[])

    # 1. Bulk-create business N:N mapping rows
    specs = [pair.spec for pair in binder.pairs]
    bulk_result = await execute_bulk_creator(db_sess, BulkCreator(specs=specs))

    # 2. Insert RBAC association rows
    values_list = [
        {
            "scope_type": pair.scope_ref.element_type.to_scope_type(),
            "scope_id": pair.scope_ref.element_id,
            "entity_type": pair.entity_ref.element_type.to_entity_type(),
            "entity_id": pair.entity_ref.element_id,
            "relation_type": pair.relation_type,
        }
        for pair in binder.pairs
    ]
    stmt = (
        pg_insert(AssociationScopesEntitiesRow)
        .values(values_list)
        .on_conflict_do_nothing()
        .returning(AssociationScopesEntitiesRow)
    )
    association_rows = list((await db_sess.scalars(stmt)).all())

    return RBACScopeBinderResult(rows=bulk_result.rows, association_rows=association_rows)


# =============================================================================
# Unbinder
# =============================================================================


class RBACScopeUnbinder[TRow: Base](ABC):
    """Abstract base for scope unbinding operations.

    Combines business row deletion (e.g., sgroups_for_domains)
    with RBAC association deletion (association_scopes_entities).

    Implementations specify what to delete by providing:
    - build_purger_spec(): Returns a BatchPurgerSpec for business N:N row deletion.
    - entity_ref: RBAC element ref for the entity to unbind (always required).
    - scope_ref: RBAC element ref for the scope to unbind from (None = all scopes).
    """

    @abstractmethod
    def build_purger_spec(self) -> BatchPurgerSpec[TRow]:
        """Build purger spec for business N:N mapping row deletion."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_ref(self) -> RBACElementRef:
        """RBAC element ref for the entity to unbind."""
        raise NotImplementedError

    @property
    @abstractmethod
    def scope_ref(self) -> RBACElementRef | None:
        """RBAC element ref for the scope to unbind from. None means all scopes."""
        raise NotImplementedError


@dataclass
class RBACScopeUnbinderResult:
    """Result of executing a scope unbinder operation.

    Attributes:
        deleted_count: Number of business N:N mapping rows deleted.
        association_rows: RBAC association rows deleted (via RETURNING).
    """

    deleted_count: int
    association_rows: list[AssociationScopesEntitiesRow]


async def execute_rbac_scope_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACScopeUnbinder[TRow],
) -> RBACScopeUnbinderResult:
    """Delete N:N mapping rows and RBAC scope associations.

    Operations:
    1. Delete business rows via unbinder.build_purger_spec()
    2. Delete RBAC associations matching unbinder.entity_ref/scope_ref

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Unbinder instance specifying purger spec and RBAC element refs.

    Returns:
        RBACScopeUnbinderResult with deletion counts and removed associations.
    """
    # 1. Delete business N:N mapping rows
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )

    # 2. Delete RBAC association rows
    entity_ref = unbinder.entity_ref
    scope_ref = unbinder.scope_ref
    conditions: list[sa.ColumnElement[bool]] = [
        AssociationScopesEntitiesRow.entity_type == entity_ref.element_type.to_entity_type(),
        AssociationScopesEntitiesRow.entity_id == entity_ref.element_id,
    ]
    if scope_ref is not None:
        conditions.append(
            AssociationScopesEntitiesRow.scope_type == scope_ref.element_type.to_scope_type(),
        )
        conditions.append(AssociationScopesEntitiesRow.scope_id == scope_ref.element_id)

    assoc_stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(*conditions)
        .returning(AssociationScopesEntitiesRow)
    )
    association_rows = list((await db_sess.scalars(assoc_stmt)).all())

    return RBACScopeUnbinderResult(
        deleted_count=purge_result.deleted_count,
        association_rows=association_rows,
    )
