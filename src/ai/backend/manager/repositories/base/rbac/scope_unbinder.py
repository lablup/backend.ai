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

from ai.backend.manager.data.permission.types import RBACElementRef
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
# Entity Unbinder
# =============================================================================


class RBACEntityUnbinder[TRow: Base](ABC):
    """Unbind entities from a scope.

    Use when removing entity-scope associations from the entity side.
    - entity_refs: Entities to unbind (batch support).
    - scope_ref: The scope to unbind from.
    """

    @abstractmethod
    def build_purger_spec(self) -> BatchPurgerSpec[TRow]:
        """Build purger spec for business N:N mapping row deletion."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_refs(self) -> Sequence[RBACElementRef]:
        """RBAC element refs for the entities to unbind."""
        raise NotImplementedError

    @property
    @abstractmethod
    def scope_ref(self) -> RBACElementRef:
        """RBAC element ref for the scope to unbind from."""
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


async def execute_rbac_entity_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACEntityUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for entities.

    Removes the business rows and the RBAC association rows
    tied to the given entities and scope.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Entity unbinder specifying purger spec and RBAC element refs.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )
    entity_refs = unbinder.entity_refs
    if not entity_refs:
        return RBACUnbinderResult(deleted_count=purge_result.deleted_count, association_rows=[])

    scope_ref = unbinder.scope_ref
    assoc_stmt = (
        sa.delete(AssociationScopesEntitiesRow)
        .where(
            AssociationScopesEntitiesRow.entity_type
            == entity_refs[0].element_type.to_entity_type(),
            AssociationScopesEntitiesRow.entity_id.in_([ref.element_id for ref in entity_refs]),
            AssociationScopesEntitiesRow.scope_type == scope_ref.element_type.to_scope_type(),
            AssociationScopesEntitiesRow.scope_id == scope_ref.element_id,
        )
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
