"""Unbinder for RBAC scope association operations.

Provides a unified unbinding ABC with execution logic for deleting
N:N mapping rows and RBAC association rows atomically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType
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
# Scope-Wide Entity Unbinder
# =============================================================================


class RBACScopeWideEntityUnbinder[TRow: Base](ABC):
    """Unbind entities of a given type from a scope.

    Use when removing entity-scope associations for a specific
    entity type and scope.
    - entity_type: The RBAC element type of entities to unbind.
    - scope_ref: The scope to unbind entities from.
    - entity_ids: Specific entity IDs to unbind, or None for all.
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
        """RBAC element ref for the scope to unbind entities from."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_ids(self) -> Sequence[str] | None:
        """Specific entity IDs to unbind, or None to unbind all."""
        raise NotImplementedError


# =============================================================================
# Result
# =============================================================================


@dataclass
class RBACUnbinderResult:
    """Result of executing an unbinder operation.

    Attributes:
        deleted_count: Number of business N:N mapping rows deleted.
        association_rows: RBAC association rows deleted (via RETURNING).
    """

    deleted_count: int
    association_rows: list[AssociationScopesEntitiesRow]


# =============================================================================
# Executor
# =============================================================================


async def execute_rbac_scope_wide_entity_unbinder[TRow: Base](
    db_sess: SASession,
    unbinder: RBACScopeWideEntityUnbinder[TRow],
) -> RBACUnbinderResult:
    """Delete N:N mapping rows and RBAC associations for an entity type in a scope.

    Removes business rows matching the purger spec and RBAC association
    rows for the given entity type and scope. When entity_ids is provided,
    only those specific entities are removed; when None, all entities of
    that type in the scope are removed.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        unbinder: Scope-wide entity unbinder specifying purger spec,
                  entity type, scope ref, and optional entity_ids.

    Returns:
        RBACUnbinderResult with deletion counts and removed associations.
    """
    purge_result = await execute_batch_purger(
        db_sess, BatchPurger(spec=unbinder.build_purger_spec())
    )
    scope_ref = unbinder.scope_ref
    where_clauses = [
        AssociationScopesEntitiesRow.entity_type == unbinder.entity_type.to_entity_type(),
        AssociationScopesEntitiesRow.scope_type == scope_ref.element_type.to_scope_type(),
        AssociationScopesEntitiesRow.scope_id == scope_ref.element_id,
    ]
    entity_ids = unbinder.entity_ids
    if entity_ids is not None:
        where_clauses.append(AssociationScopesEntitiesRow.entity_id.in_(entity_ids))
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
