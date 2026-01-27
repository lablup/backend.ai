"""Creator for RBAC scope-scoped entity insert operations."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single Entity Creator
# =============================================================================


@dataclass
class RBACEntityCreator[TRow: Base]:
    """Creator for a single entity with scope associations for RBAC.

    Creates an entity row and associates it with one or more permission scopes.
    The primary scope is required; additional scopes are optional.

    Attributes:
        spec: CreatorSpec implementation defining the row to create.
        entity_type: The entity type for RBAC association.
        scope_ref: Primary scope reference (scope_type + scope_id) for this entity.
        additional_scope_refs: Additional scope references for multi-scope entities.
    """

    spec: CreatorSpec[TRow]
    entity_type: EntityType
    scope_ref: ScopeId
    additional_scope_refs: Sequence[ScopeId] = field(default_factory=list)


@dataclass
class RBACEntityCreatorResult[TRow: Base]:
    """Result of executing a single entity creation."""

    row: TRow


async def execute_rbac_entity_creator[TRow: Base](
    db_sess: SASession,
    creator: RBACEntityCreator[TRow],
) -> RBACEntityCreatorResult[TRow]:
    """Create a scope-scoped entity with its scope association.

    Operations:
    1. Insert main entity row
    2. Flush to get DB-generated ID
    3. Extract RBAC info from spec
    4. Insert AssociationScopesEntitiesRow (scope -> entity mapping)

    The AssociationScopesEntitiesRow maps the entity to its owning scope,
    enabling scope-based entity discovery and permission inheritance.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        creator: Creator instance with spec defining the entity to create.

    Returns:
        RBACEntityCreatorResult containing the created row.
    """
    spec = creator.spec
    row = spec.build_row()
    mapper = inspect(type(row))
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 1. Build and insert row
    db_sess.add(row)

    # 2. Flush to get DB-generated ID
    await db_sess.flush()

    # 3. Extract RBAC info and insert associations for all scopes
    instance_state = inspect(row)
    pk_value = instance_state.identity[0]
    all_scope_refs = [creator.scope_ref, *creator.additional_scope_refs]
    for scope_ref in all_scope_refs:
        db_sess.add(
            AssociationScopesEntitiesRow(
                scope_type=scope_ref.scope_type,
                scope_id=scope_ref.scope_id,
                entity_type=creator.entity_type,
                entity_id=str(pk_value),
            ),
        )

    return RBACEntityCreatorResult(row=row)


# =============================================================================
# Bulk Entity Creator
# =============================================================================


@dataclass
class RBACBulkEntityCreator[TRow: Base]:
    """Bulk creator for multiple entities with a single shared scope.

    Attributes:
        specs: Sequence of CreatorSpec implementations.
        scope_type: The scope type for all entities.
        scope_id: The scope ID for all entities.
        entity_type: The entity type for all entities.
    """

    specs: Sequence[CreatorSpec[TRow]]
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType


@dataclass
class RBACBulkEntityCreatorResult[TRow: Base]:
    """Result of executing a bulk entity creation."""

    rows: list[TRow]


async def execute_rbac_bulk_entity_creator[TRow: Base](
    db_sess: SASession,
    creator: RBACBulkEntityCreator[TRow],
) -> RBACBulkEntityCreatorResult[TRow]:
    """Create multiple scope-scoped entities in a single transaction.

    Operations:
    1. Build and insert all entity rows
    2. Flush to get DB-generated IDs
    3. Bulk insert AssociationScopesEntitiesRows

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        creator: Bulk creator with specs defining entities to create.

    Returns:
        RBACBulkEntityCreatorResult containing all created rows.
    """
    if not creator.specs:
        return RBACBulkEntityCreatorResult(rows=[])

    # 1. Build and add all rows
    rows = [spec.build_row() for spec in creator.specs]
    db_sess.add_all(rows)

    mapper = inspect(type(rows[0]))
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 2. Flush to get DB-generated IDs and insert associations
    await db_sess.flush()

    associations = [
        AssociationScopesEntitiesRow(
            scope_type=creator.scope_type,
            scope_id=creator.scope_id,
            entity_type=creator.entity_type,
            entity_id=str(inspect(row).identity[0]),
        )
        for row in rows
    ]
    db_sess.add_all(associations)

    return RBACBulkEntityCreatorResult(rows=rows)
