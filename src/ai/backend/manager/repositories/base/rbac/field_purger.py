"""Purger for RBAC field-scoped entity delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from typing import Generic, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import FieldRef
from ai.backend.manager.data.permission.types import FieldType
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec as BaseBatchPurgerSpec
from ai.backend.manager.repositories.base.purger import Purger as BasePurger
from ai.backend.manager.repositories.base.purger import PurgerResult as BasePurgerResult
from ai.backend.manager.repositories.base.purger import TRow

# =============================================================================
# Spec Classes (Batch Only)
# =============================================================================


class RBACFieldBatchPurgerSpec(BaseBatchPurgerSpec[TRow], ABC):
    """Spec for RBAC field batch purge operations.

    Inherits build_subquery() from BaseBatchPurgerSpec.
    Implementations must provide:
    - field_type(): Returns the FieldType for constructing FieldRefs from row PKs
    """

    @abstractmethod
    def field_type(self) -> FieldType:
        """Return the field type for constructing FieldRefs from row primary keys."""
        raise NotImplementedError


# =============================================================================
# Purger Classes
# =============================================================================


@dataclass
class RBACFieldPurger(BasePurger[TRow]):
    """Single-row RBAC field purger by primary key.

    Inherits row_class and pk_value from BasePurger.

    Attributes:
        field_type: The field type for RBAC cleanup.
        field_id: The field ID to delete.
    """

    field_type: FieldType
    field_id: str


@dataclass
class RBACFieldPurgerResult(BasePurgerResult[TRow]):
    """Result of executing a single-row RBAC field purge."""

    pass


@dataclass
class RBACFieldBatchPurger(Generic[TRow]):
    """Batch purger for RBAC field-scoped entities.

    Attributes:
        spec: RBACFieldBatchPurgerSpec implementation defining what to delete.
        batch_size: Batch size for chunked deletion (default: 1000).
    """

    spec: RBACFieldBatchPurgerSpec[TRow]
    batch_size: int = 1000


@dataclass
class RBACFieldBatchPurgerResult:
    """Result of RBAC field batch purge operation."""

    deleted_count: int
    deleted_entity_field_count: int


# =============================================================================
# Deletion Helpers (Single Field)
# =============================================================================


async def _delete_entity_field(
    db_sess: SASession,
    field: FieldRef,
) -> None:
    """Delete EntityFieldRow for the given field."""
    await db_sess.execute(
        sa.delete(EntityFieldRow).where(
            sa.and_(
                EntityFieldRow.field_id == field.field_id,
                EntityFieldRow.field_type == field.field_type,
            )
        )
    )


# =============================================================================
# Deletion Helpers (Batch) - Return counts
# =============================================================================


async def _batch_delete_entity_fields(
    db_sess: SASession,
    field_ids: Collection[FieldRef],
) -> int:
    """Delete EntityFieldRows for multiple fields. Returns count of deleted rows."""
    if not field_ids:
        return 0

    conditions = [
        sa.and_(
            EntityFieldRow.field_id == fid.field_id,
            EntityFieldRow.field_type == fid.field_type,
        )
        for fid in field_ids
    ]

    result = await db_sess.execute(sa.delete(EntityFieldRow).where(sa.or_(*conditions)))
    return cast(CursorResult, result).rowcount or 0


# =============================================================================
# Orchestration
# =============================================================================


async def _delete_row_by_pk_returning(
    db_sess: SASession,
    purger: RBACFieldPurger[TRow],
) -> TRow | None:
    """Delete a row by primary key and return the deleted row data."""
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    stmt = sa.delete(table).where(pk_columns[0] == purger.pk_value).returning(*table.columns)
    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    return row_class(**dict(row_data._mapping))


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_field_purger(
    db_sess: SASession,
    purger: RBACFieldPurger[TRow],
) -> RBACFieldPurgerResult[TRow] | None:
    """
    Execute DELETE for a single field-scoped entity by primary key, along with related RBAC entries.

    Operations performed:
    1. Build FieldRef from purger params
    2. Delete EntityFieldRow (field-entity mapping)
    3. Delete the main object row with RETURNING

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: Purger containing row_class, pk_value, field_type, and field_id

    Returns:
        RBACFieldPurgerResult containing the deleted row, or None if no row matched
    """
    # 1. Build FieldRef from flat params
    field_ref = FieldRef(field_type=purger.field_type, field_id=purger.field_id)

    # 2. Delete RBAC entries (EntityFieldRow)
    await _delete_entity_field(db_sess, field_ref)

    # 3. Delete main row with RETURNING
    row = await _delete_row_by_pk_returning(db_sess, purger)
    if row is None:
        return None

    return RBACFieldPurgerResult(row=row)


async def execute_rbac_field_batch_purger(
    db_sess: SASession,
    purger: RBACFieldBatchPurger[TRow],
) -> RBACFieldBatchPurgerResult:
    """
    Execute batch DELETE for field-scoped entities with RBAC cleanup.

    Deletes rows in batches, cleaning up related RBAC entries for each batch:
    - EntityFieldRows for field_ids

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: BatchPurger containing spec and batch configuration

    Returns:
        RBACFieldBatchPurgerResult with counts of deleted rows
    """
    total_deleted = 0
    total_entity_field = 0

    # Get table and PK info from subquery
    base_subquery = purger.spec.build_subquery()
    table = cast(sa.Table, base_subquery.froms[0])
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Batch purger only supports single-column primary keys (table: {table.name})",
        )

    pk_col = pk_columns[0]
    field_type = purger.spec.field_type()

    while True:
        # 1. DELETE with RETURNING - get PKs and delete in one query
        sub = purger.spec.build_subquery().subquery()
        pk_subquery = sa.select(sub.c[pk_col.key]).limit(purger.batch_size)

        stmt = sa.delete(table).where(pk_col.in_(pk_subquery)).returning(pk_col)
        result = await db_sess.execute(stmt)
        deleted_pks = result.fetchall()

        if not deleted_pks:
            break

        pk_values = [row[0] for row in deleted_pks]
        batch_deleted = len(pk_values)
        total_deleted += batch_deleted

        # 2. Construct field_ids from deleted PKs
        field_ids: list[FieldRef] = [
            FieldRef(field_type=field_type, field_id=str(pk)) for pk in pk_values
        ]

        # 3. Clean up RBAC entries (after main row deletion - no FK constraint)
        total_entity_field += await _batch_delete_entity_fields(db_sess, field_ids)

        if batch_deleted < purger.batch_size:
            break

    return RBACFieldBatchPurgerResult(
        deleted_count=total_deleted,
        deleted_entity_field_count=total_entity_field,
    )
