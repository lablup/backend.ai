"""Creator for RBAC field-scoped entity insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import FieldRef, ObjectId
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.creator import CreatorSpec

from .utils import bulk_insert_on_conflict_do_nothing, insert_on_conflict_do_nothing

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACField:
    """Represents an RBAC field belonging to a parent entity.

    Attributes:
        parent_entity: ObjectId representing the parent entity.
        field: FieldRef representing the field itself.
    """

    parent_entity: ObjectId
    field: FieldRef


# =============================================================================
# Field Creator Spec
# =============================================================================


class RBACFieldCreatorSpec(CreatorSpec[TRow], ABC):
    """Spec for building a field-scoped entity row.

    Implementations specify what field to create by providing:
    - build_row(): Build domain row (ID can use DB server_default)
    - field(row): Extract RBAC field info from flushed row

    The executor combines these to create the entity-field mapping.
    """

    @abstractmethod
    def field(self, row: TRow) -> RBACField:
        """Extract RBAC field information from flushed row.

        Args:
            row: Flushed ORM row (with ID assigned).

        Returns:
            RBACField containing parent entity and field information.
        """
        raise NotImplementedError


# =============================================================================
# Single Field Creator
# =============================================================================


async def _insert_entity_field_mapping(
    db_sess: SASession,
    rbac_field: RBACField,
) -> None:
    """Insert a single entity-field mapping."""
    await insert_on_conflict_do_nothing(
        db_sess,
        EntityFieldRow(
            entity_type=rbac_field.parent_entity.entity_type,
            entity_id=rbac_field.parent_entity.entity_id,
            field_type=rbac_field.field.field_type,
            field_id=rbac_field.field.field_id,
        ),
    )


@dataclass
class RBACFieldCreator(Generic[TRow]):
    """Creator for a single field-scoped entity.

    Attributes:
        spec: RBACFieldCreatorSpec implementation defining what to create.
    """

    spec: RBACFieldCreatorSpec[TRow]


@dataclass
class RBACFieldCreatorResult(Generic[TRow]):
    """Result of executing a single field creation."""

    row: TRow


async def execute_rbac_field_creator(
    db_sess: SASession,
    creator: RBACFieldCreator[TRow],
) -> RBACFieldCreatorResult[TRow]:
    """Create a field-scoped entity with its entity-field mapping.

    Operations:
    1. Insert main field row
    2. Flush to get DB-generated ID
    3. Extract RBAC info from spec
    4. Insert EntityFieldRow (parent_entity -> field mapping)

    The EntityFieldRow maps the field to its parent entity,
    enabling entity-field relationship tracking.

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        creator: Creator instance with spec defining the field to create.

    Returns:
        RBACFieldCreatorResult containing the created row.
    """
    spec = creator.spec

    # 1. Build and insert row
    row = spec.build_row()
    db_sess.add(row)

    # 2. Flush to get DB-generated ID
    await db_sess.flush()
    await db_sess.refresh(row)

    # 3. Extract RBAC info and insert entity-field mapping
    await _insert_entity_field_mapping(db_sess, spec.field(row))

    return RBACFieldCreatorResult(row=row)


# =============================================================================
# Bulk Field Creator
# =============================================================================


async def _bulk_insert_entity_field_mappings(
    db_sess: SASession,
    rbac_fields: Sequence[RBACField],
) -> None:
    """Bulk insert entity-field mappings."""
    entity_fields = [
        EntityFieldRow(
            entity_type=rbac_field.parent_entity.entity_type,
            entity_id=rbac_field.parent_entity.entity_id,
            field_type=rbac_field.field.field_type,
            field_id=rbac_field.field.field_id,
        )
        for rbac_field in rbac_fields
    ]
    await bulk_insert_on_conflict_do_nothing(db_sess, entity_fields)


@dataclass
class RBACBulkFieldCreator(Generic[TRow]):
    """Bulk creator for multiple field-scoped entities.

    Attributes:
        specs: Sequence of RBACFieldCreatorSpec implementations.
    """

    specs: Sequence[RBACFieldCreatorSpec[TRow]]


@dataclass
class RBACBulkFieldCreatorResult(Generic[TRow]):
    """Result of executing a bulk field creation."""

    rows: list[TRow]


async def execute_rbac_bulk_field_creator(
    db_sess: SASession,
    creator: RBACBulkFieldCreator[TRow],
) -> RBACBulkFieldCreatorResult[TRow]:
    """Create multiple field-scoped entities in a single transaction.

    Operations:
    1. Build and insert all field rows
    2. Flush to get DB-generated IDs
    3. Bulk insert EntityFieldRows

    Args:
        db_sess: Async SQLAlchemy session (must be writable).
        creator: Bulk creator with specs defining fields to create.

    Returns:
        RBACBulkFieldCreatorResult containing all created rows.
    """
    if not creator.specs:
        return RBACBulkFieldCreatorResult(rows=[])

    # 1. Build and add all rows
    rows: list[TRow] = []
    for spec in creator.specs:
        row = spec.build_row()
        db_sess.add(row)
        rows.append(row)

    # 2. Flush to get DB-generated IDs
    await db_sess.flush()

    # 3. Extract RBAC fields and insert entity-field mappings
    rbac_fields = [spec.field(row) for spec, row in zip(creator.specs, rows, strict=False)]
    await _bulk_insert_entity_field_mappings(db_sess, rbac_fields)

    return RBACBulkFieldCreatorResult(rows=rows)
