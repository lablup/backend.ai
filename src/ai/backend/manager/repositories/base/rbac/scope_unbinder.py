"""Unbinder for RBAC scope association operations.

Provides entity-centric and scope-centric unbinding ABCs
with shared execution logic for deleting N:N mapping rows
and RBAC association rows atomically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.types import RBACElementRef, RBACElementType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.purger import (
    BatchPurger,
    BatchPurgerSpec,
    execute_batch_purger,
)

# =============================================================================
# Scope-Wide Entity Unbinder
# =============================================================================


class RBACScopeWideEntityUnbinder[TRow: Base](ABC):
    """Unbind entities from a scope, with optional entity filtering.

    Use when removing entity-scope associations from the scope side.
    - entity_ids=None: delete ALL entities of entity_type within the scope.
    - entity_ids=Sequence[str]: delete only the specified entities.
    """

    @abstractmethod
    def build_purger_spec(self) -> BatchPurgerSpec[TRow]:
        """Build purger spec for business N:N mapping row deletion."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_type(self) -> RBACElementType:
        """RBAC element type of the entities to unbind."""
        raise NotImplementedError

    @property
    @abstractmethod
    def scope_ref(self) -> RBACElementRef:
        """RBAC element ref for the scope to unbind from."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_ids(self) -> Sequence[str] | None:
        """Entity IDs to unbind.

        None means delete all entities of entity_type within the scope.
        A sequence means delete only the specified entity IDs.
        """
        raise NotImplementedError


# =============================================================================
# Scope Unbinder
# =============================================================================


class RBACScopeUnbinder[TRow: Base](ABC):
    """Unbind scopes from an entity.

    Use when removing entity-scope associations from the scope side.
    - scope_refs: Scopes to unbind (batch support).
    - entity_ref: The entity to unbind from.
    """

    @abstractmethod
    def build_purger_spec(self) -> BatchPurgerSpec[TRow]:
        """Build purger spec for business N:N mapping row deletion."""
        raise NotImplementedError

    @property
    @abstractmethod
    def scope_refs(self) -> Sequence[RBACElementRef]:
        """RBAC element refs for the scopes to unbind from."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_ref(self) -> RBACElementRef:
        """RBAC element ref for the entity to unbind."""
        raise NotImplementedError


# =============================================================================
# Result
# =============================================================================


@dataclass
class RBACUnbinderResult:
    """Result of executing an unbinder operation (entity or scope).

    Attributes:
        deleted_count: Number of business N:N mapping rows deleted.
        association_rows: RBAC association rows deleted (via RETURNING).
    """

    deleted_count: int
    association_rows: list[AssociationScopesEntitiesRow]


# =============================================================================
# Executors
# =============================================================================


async def execute_rbac_scope_wide_entity_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACScopeWideEntityUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for entities within a scope.

    Removes the business rows and the RBAC association rows
    tied to the given entities and scope.  When entity_ids is None,
    all entities of the given entity_type within the scope are deleted.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Scope-wide entity unbinder specifying purger spec and RBAC element refs.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )

    scope_ref = unbinder.scope_ref
    where_clauses: list[sa.ColumnElement[bool]] = [
        AssociationScopesEntitiesRow.entity_type == unbinder.entity_type.to_entity_type(),
        AssociationScopesEntitiesRow.scope_type == scope_ref.element_type.to_scope_type(),
        AssociationScopesEntitiesRow.scope_id == scope_ref.element_id,
    ]
    if unbinder.entity_ids is not None:
        where_clauses.append(
            AssociationScopesEntitiesRow.entity_id.in_(unbinder.entity_ids),
        )

    assoc_stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(*where_clauses)
        .returning(AssociationScopesEntitiesRow)
    )
    association_rows = list((await db_sess.scalars(assoc_stmt)).all())
    return RBACUnbinderResult(
        deleted_count=purge_result.deleted_count,
        association_rows=association_rows,
    )


async def execute_rbac_scope_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACScopeUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for scopes.

    Removes the business rows and the RBAC association rows
    tied to the given scopes and entity.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Scope unbinder specifying purger spec and RBAC element refs.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )
    scope_refs = unbinder.scope_refs
    if not scope_refs:
        return RBACUnbinderResult(deleted_count=purge_result.deleted_count, association_rows=[])

    entity_ref = unbinder.entity_ref
    assoc_stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(
            AssociationScopesEntitiesRow.entity_type == entity_ref.element_type.to_entity_type(),
            AssociationScopesEntitiesRow.entity_id == entity_ref.element_id,
            AssociationScopesEntitiesRow.scope_type == scope_refs[0].element_type.to_scope_type(),
            AssociationScopesEntitiesRow.scope_id.in_([ref.element_id for ref in scope_refs]),
        )
        .returning(AssociationScopesEntitiesRow)
    )
    association_rows = list((await db_sess.scalars(assoc_stmt)).all())
    return RBACUnbinderResult(
        deleted_count=purge_result.deleted_count,
        association_rows=association_rows,
    )
