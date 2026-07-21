"""Creator for RBAC scope-scoped entity insert operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypeVar

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import BulkCreatorError, CreatorSpec
from ai.backend.manager.repositories.base.integrity import (
    match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single Entity Creator
# =============================================================================


@dataclass
class RBACEntityCreator[TRow: Base]:
    """Creator for a single entity with scope associations for RBAC.

    Creates an entity row and associates it with the permission scopes it belongs to.
    A ``scope_ref`` of ``None`` marks the entity as GLOBAL — outside the RBAC scope
    hierarchy — so it binds to no scope at all and its create is a plain insert.

    Attributes:
        spec: CreatorSpec implementation defining the row to create.
        element_type: The RBAC element type for this entity.
        scope_ref: Primary scope reference (scope_type + scope_id) for this entity, or
            ``None`` for a GLOBAL entity. A GLOBAL entity has no scope to associate, so
            ``additional_scope_refs`` and ``relation_type`` do not apply to it and are
            ignored.
        additional_scope_refs: Additional scope references for multi-scope entities.
            Only meaningful alongside a ``scope_ref``.
        relation_type: The relation type for the scope-entity association. Defaults to AUTO.
    """

    spec: CreatorSpec[TRow]
    element_type: RBACElementType
    scope_ref: RBACElementRef | None
    additional_scope_refs: Sequence[RBACElementRef] = field(default_factory=list)
    relation_type: RelationType = RelationType.AUTO

    def all_scope_refs(self) -> list[RBACElementRef]:
        """Every scope this entity binds to; empty for a GLOBAL entity (``scope_ref=None``)."""
        if self.scope_ref is None:
            return []
        return [self.scope_ref, *self.additional_scope_refs]


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
    enabling scope-based entity discovery and permission inheritance. A creator that
    binds to no scope (see :attr:`RBACEntityCreator.scope_ref`) skips step 4, making
    this a plain insert.

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
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, spec.integrity_error_checks)

    # 3. Extract RBAC info and insert associations for all scopes
    instance_state = inspect(row)
    pk_value = instance_state.identity[0]
    entity_type = creator.element_type.to_entity_type()
    associations = [
        AssociationScopesEntitiesRow(
            scope_type=scope_ref.element_type.to_scope_type(),
            scope_id=scope_ref.element_id,
            entity_type=entity_type,
            entity_id=str(pk_value),
            relation_type=creator.relation_type,
        )
        for scope_ref in creator.all_scope_refs()
    ]
    await bulk_insert_on_conflict_do_nothing(db_sess, associations)

    return RBACEntityCreatorResult(row=row)


@dataclass
class RBACBulkEntityCreatorResultWithFailures[TRow: Base]:
    """Result of a scoped bulk create that isolates each entity.

    Mirrors :class:`BulkCreatorResultWithFailures`. ``errors`` index into the sequence of
    creators handed to the executor, not into any list the caller may have derived it from.
    """

    successes: list[TRow]
    errors: list[BulkCreatorError[TRow]]


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
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        # Use first spec's checks (all specs share the same CreatorSpec subclass)
        checks = creator.specs[0].integrity_error_checks
        match_integrity_error(parsed, checks)

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
    await bulk_insert_on_conflict_do_nothing(db_sess, associations)

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
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        # Use first creator's spec checks (all creators share the same CreatorSpec subclass)
        checks = creators[0].spec.integrity_error_checks
        match_integrity_error(parsed, checks)

    # 3. Collect all associations from each creator's scope refs
    associations: list[AssociationScopesEntitiesRow] = []
    for creator, row in zip(creators, rows, strict=True):
        pk_value = inspect(row).identity[0]
        entity_type = creator.element_type.to_entity_type()
        for scope_ref in creator.all_scope_refs():
            associations.append(
                AssociationScopesEntitiesRow(
                    scope_type=scope_ref.element_type.to_scope_type(),
                    scope_id=scope_ref.element_id,
                    entity_type=entity_type,
                    entity_id=str(pk_value),
                    relation_type=creator.relation_type,
                ),
            )
    await bulk_insert_on_conflict_do_nothing(db_sess, associations)

    return RBACBulkEntityCreatorResult(rows=rows)
