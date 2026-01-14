"""Creator for RBAC field-scoped entity insert operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.creator import CreatorSpec

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single Field Creator
# =============================================================================


@dataclass
class RBACFieldCreator(Generic[TRow]):
    """Creator for a single field-scoped entity.

    Attributes:
        spec: CreatorSpec implementation defining the row to create.
        entity_type: The entity type of the parent entity.
        entity_id: The ID of the parent entity.
        field_type: The field type for RBAC field mapping.
    """

    spec: CreatorSpec[TRow]
    entity_type: EntityType
    entity_id: str
    field_type: EntityType


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
    3. Extract field ID from row
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
    row = spec.build_row()
    mapper = inspect(type(row))
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Creator only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 1. Build and insert row
    db_sess.add(row)

    # 2. Flush to get DB-generated ID
    await db_sess.flush()

    # 3. Extract field ID and insert entity-field mapping
    instance_state = inspect(row)
    pk_value = instance_state.identity[0]
    db_sess.add(
        EntityFieldRow(
            entity_type=creator.entity_type,
            entity_id=creator.entity_id,
            field_type=creator.field_type,
            field_id=str(pk_value),
        )
    )

    return RBACFieldCreatorResult(row=row)


# =============================================================================
# Bulk Field Creator
# =============================================================================


@dataclass
class RBACBulkFieldCreator(Generic[TRow]):
    """Bulk creator for multiple field-scoped entities.

    Attributes:
        specs: Sequence of CreatorSpec implementations.
        entity_type: The entity type of the parent entity for all fields.
        entity_id: The ID of the parent entity for all fields.
        field_type: The field type for all fields.
    """

    specs: Sequence[CreatorSpec[TRow]]
    entity_type: EntityType
    entity_id: str
    field_type: EntityType


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
    rows = [spec.build_row() for spec in creator.specs]
    db_sess.add_all(rows)

    mapper = inspect(type(rows[0]))
    pk_columns = mapper.primary_key
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Creator only supports single-column primary keys (table: {mapper.local_table.name})",
        )

    # 2. Flush to get DB-generated IDs and insert field mappings
    await db_sess.flush()

    field_rows = [
        EntityFieldRow(
            entity_type=creator.entity_type,
            entity_id=creator.entity_id,
            field_type=creator.field_type,
            field_id=str(inspect(row).identity[0]),
        )
        for row in rows
    ]
    db_sess.add_all(field_rows)

    return RBACBulkFieldCreatorResult(rows=rows)
