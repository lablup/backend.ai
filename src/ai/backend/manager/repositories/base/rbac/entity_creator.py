"""Creator for RBAC scope-scoped entity insert operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
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
        element_type: The RBAC element type for this entity.
        scope_ref: Primary scope reference (scope_type + scope_id) for this entity.
        additional_scope_refs: Additional scope references for multi-scope entities.
        relation_type: The relation type for the scope-entity association. Defaults to AUTO.
    """

    spec: CreatorSpec[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef
    additional_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    relation_type: RelationType = RelationType.AUTO


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
            f"Entity creator only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 1. Build and insert row
    db_sess.add(row)

    # 2. Flush to get DB-generated ID
    await db_sess.flush()

    # 3. Extract RBAC info and insert associations for all scopes
    instance_state = inspect(row)
    pk_value = instance_state.identity[0]
    entity_type = creator.element_type.to_entity_type()
    all_scope_refs = [creator.scope_ref, *creator.additional_scope_refs]
    for scope_ref in all_scope_refs:
        db_sess.add(
            AssociationScopesEntitiesRow(
                scope_type=scope_ref.element_type.to_scope_type(),
                scope_id=scope_ref.element_id,
                entity_type=entity_type,
                entity_id=str(pk_value),
                relation_type=creator.relation_type,
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
        element_type: The RBAC element type for all entities.
        scope_ref: The scope reference (scope_type + scope_id) for all entities.
        relation_type: The relation type for the scope-entity association. Defaults to AUTO.
    """

    specs: Sequence[CreatorSpec[TRow]]
    element_type: RBACElementType
    scope_ref: RBACElementRef
    relation_type: RelationType = RelationType.AUTO


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
            f"Entity creator only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 2. Flush to get DB-generated IDs and insert associations
    await db_sess.flush()

    entity_type = creator.element_type.to_entity_type()
    associations = [
        AssociationScopesEntitiesRow(
            scope_type=creator.scope_ref.element_type.to_scope_type(),
            scope_id=creator.scope_ref.element_id,
            entity_type=entity_type,
            entity_id=str(inspect(row).identity[0]),
            relation_type=creator.relation_type,
        )
        for row in rows
    ]
    db_sess.add_all(associations)

    return RBACBulkEntityCreatorResult(rows=rows)


async def execute_rbac_entity_creators[TRow: Base](
    db_sess: SASession,
    creators: Sequence[RBACEntityCreator[TRow]],
) -> RBACBulkEntityCreatorResult[TRow]:
    """Create multiple entities from individual RBACEntityCreator instances in a single batch.

    Unlike execute_rbac_bulk_entity_creator which shares a single scope across all entities,
    this function accepts a sequence of RBACEntityCreator instances where each entity can have
    its own primary scope and additional scope references.

    Operations:
    1. Build and insert all entity rows from each creator's spec
    2. Single flush to get all DB-generated IDs
    3. Collect all scope associations (primary + additional per entity), bulk insert
    4. Return RBACBulkEntityCreatorResult with all rows

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        creators: Sequence of RBACEntityCreator instances, each with its own scope refs.

    Returns:
        RBACBulkEntityCreatorResult containing all created rows.
    """
    if not creators:
        return RBACBulkEntityCreatorResult(rows=[])

    # 1. Build and add all rows
    rows = [creator.spec.build_row() for creator in creators]
    db_sess.add_all(rows)

    mapper = inspect(type(rows[0]))
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Entity creator only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 2. Single flush to get all DB-generated IDs
    await db_sess.flush()

    # 3. Collect all associations from each creator's scope refs
    associations: list[AssociationScopesEntitiesRow] = []
    for creator, row in zip(creators, rows, strict=True):
        pk_value = inspect(row).identity[0]
        entity_type = creator.element_type.to_entity_type()
        all_scope_refs = [creator.scope_ref, *creator.additional_scope_refs]
        for scope_ref in all_scope_refs:
            associations.append(
                AssociationScopesEntitiesRow(
                    scope_type=scope_ref.element_type.to_scope_type(),
                    scope_id=scope_ref.element_id,
                    entity_type=entity_type,
                    entity_id=str(pk_value),
                    relation_type=creator.relation_type,
                ),
            )
    db_sess.add_all(associations)

    return RBACBulkEntityCreatorResult(rows=rows)
