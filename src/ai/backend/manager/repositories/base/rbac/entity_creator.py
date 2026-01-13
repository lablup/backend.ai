"""Creator for RBAC scope-scoped entity insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec

from .utils import bulk_insert_on_conflict_do_nothing, insert_on_conflict_do_nothing

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACEntity:
    """Represents an RBAC-scoped entity.

    Attributes:
        scope: ScopeId representing the scope the entity belongs to.
        entity: ObjectId representing the entity itself.
    """

    scope: ScopeId
    entity: ObjectId


# =============================================================================
# Entity Creator Spec
# =============================================================================


class RBACEntityCreatorSpec(CreatorSpec[TRow], ABC):
    """Spec for building a scope-scoped entity row.

    Implementations specify what entity to create by providing:
    - build_row(): Build domain row (ID can use DB server_default)
    - entity(row): Extract RBAC entity info from flushed row

    The executor combines these to create the RBAC association.
    """

    @abstractmethod
    def entity(self, row: TRow) -> RBACEntity:
        """Extract RBAC entity information from flushed row.

        Args:
            row: Flushed ORM row (with ID assigned).

        Returns:
            RBACEntity containing scope and entity information.
        """
        raise NotImplementedError


# =============================================================================
# Single Entity Creator
# =============================================================================


async def _insert_scope_entity_association(
    db_sess: SASession,
    rbac_entity: RBACEntity,
) -> None:
    """Insert a single scope-entity association."""
    await insert_on_conflict_do_nothing(
        db_sess,
        AssociationScopesEntitiesRow(
            scope_type=rbac_entity.scope.scope_type,
            scope_id=rbac_entity.scope.scope_id,
            entity_type=rbac_entity.entity.entity_type,
            entity_id=rbac_entity.entity.entity_id,
        ),
    )


@dataclass
class RBACEntityCreator(Generic[TRow]):
    """Creator for a single scope-scoped entity.

    Attributes:
        spec: RBACEntityCreatorSpec implementation defining what to create.
    """

    spec: RBACEntityCreatorSpec[TRow]


@dataclass
class RBACEntityCreatorResult(Generic[TRow]):
    """Result of executing a single entity creation."""

    row: TRow


async def execute_rbac_entity_creator(
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

    # 1. Build and insert row
    row = spec.build_row()
    db_sess.add(row)

    # 2. Flush to get DB-generated ID
    await db_sess.flush()
    await db_sess.refresh(row)

    # 3. Extract RBAC info and insert association
    await _insert_scope_entity_association(db_sess, spec.entity(row))

    return RBACEntityCreatorResult(row=row)


# =============================================================================
# Bulk Entity Creator
# =============================================================================


async def _bulk_insert_scope_entity_associations(
    db_sess: SASession,
    rbac_entities: Sequence[RBACEntity],
) -> None:
    """Bulk insert scope-entity associations."""
    associations = [
        AssociationScopesEntitiesRow(
            scope_type=rbac_entity.scope.scope_type,
            scope_id=rbac_entity.scope.scope_id,
            entity_type=rbac_entity.entity.entity_type,
            entity_id=rbac_entity.entity.entity_id,
        )
        for rbac_entity in rbac_entities
    ]
    await bulk_insert_on_conflict_do_nothing(db_sess, associations)


@dataclass
class RBACBulkEntityCreator(Generic[TRow]):
    """Bulk creator for multiple scope-scoped entities.

    Attributes:
        specs: Sequence of RBACEntityCreatorSpec implementations.
    """

    specs: Sequence[RBACEntityCreatorSpec[TRow]]


@dataclass
class RBACBulkEntityCreatorResult(Generic[TRow]):
    """Result of executing a bulk entity creation."""

    rows: list[TRow]


async def execute_rbac_bulk_entity_creator(
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
    rows: list[TRow] = []
    for spec in creator.specs:
        row = spec.build_row()
        db_sess.add(row)
        rows.append(row)

    # 2. Flush to get DB-generated IDs
    await db_sess.flush()

    # 3. Extract RBAC entities and insert associations
    rbac_entities = [spec.entity(row) for spec, row in zip(creator.specs, rows, strict=False)]
    await _bulk_insert_scope_entity_associations(db_sess, rbac_entities)

    return RBACBulkEntityCreatorResult(rows=rows)
