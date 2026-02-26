"""Unbinder for RBAC scope association operations.

Provides entity-centric and scope-centric unbinding ABCs
with shared execution logic for deleting N:N mapping rows
and RBAC association rows atomically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
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
    """Unbind a specific entity from scope associations.

    Use when deleting an entity and its scope bindings.
    - entity_ref: The entity to unbind (required).
    - scope_ref: Specific scope to unbind from (None = all scopes).
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


# =============================================================================
# Scope Unbinder
# =============================================================================


class RBACScopeUnbinder[TRow: Base](ABC):
    """Unbind entities from a specific scope.

    Use when deleting a scope and its entity bindings.
    - scope_ref: The scope to unbind from (required).
    - entity_ref: Specific entity to unbind (None = all entities).
    """

    @abstractmethod
    def build_purger_spec(self) -> BatchPurgerSpec[TRow]:
        """Build purger spec for business N:N mapping row deletion."""
        raise NotImplementedError

    @property
    @abstractmethod
    def scope_ref(self) -> RBACElementRef:
        """RBAC element ref for the scope to unbind from."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_ref(self) -> RBACElementRef | None:
        """RBAC element ref for the entity to unbind. None means all entities."""
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


async def _delete_rbac_associations(
    db_sess: SASession,
    entity_ref: RBACElementRef | None,
    scope_ref: RBACElementRef | None,
) -> list[AssociationScopesEntitiesRow]:
    """Delete RBAC association rows matching the given entity/scope refs.

    At least one of entity_ref or scope_ref must be provided.
    """
    conditions: list[sa.ColumnElement[bool]] = []
    if entity_ref is not None:
        conditions.append(
            AssociationScopesEntitiesRow.entity_type == entity_ref.element_type.to_entity_type(),
        )
        conditions.append(AssociationScopesEntitiesRow.entity_id == entity_ref.element_id)
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
    return list((await db_sess.scalars(assoc_stmt)).all())


async def execute_rbac_entity_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACEntityUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for an entity.

    Use when deleting an entity: removes the business rows and
    the RBAC association rows tied to that entity.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Entity unbinder specifying purger spec and RBAC element refs.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )
    association_rows = await _delete_rbac_associations(
        db_sess, entity_ref=unbinder.entity_ref, scope_ref=unbinder.scope_ref
    )
    return RBACUnbinderResult(
        deleted_count=purge_result.deleted_count,
        association_rows=association_rows,
    )


async def execute_rbac_scope_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACScopeUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for a scope.

    Use when deleting a scope: removes the business rows and
    the RBAC association rows tied to that scope.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Scope unbinder specifying purger spec and RBAC element refs.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )
    association_rows = await _delete_rbac_associations(
        db_sess, entity_ref=unbinder.entity_ref, scope_ref=unbinder.scope_ref
    )
    return RBACUnbinderResult(
        deleted_count=purge_result.deleted_count,
        association_rows=association_rows,
    )
