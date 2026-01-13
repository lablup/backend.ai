"""Purger for RBAC field-scoped entity delete operations."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Generic, Protocol, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import FieldRef
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec as BaseBatchPurgerSpec
from ai.backend.manager.repositories.base.purger import Purger as BasePurger
from ai.backend.manager.repositories.base.purger import PurgerResult as BasePurgerResult
from ai.backend.manager.repositories.base.purger import TRow

# =============================================================================
# Protocol
# =============================================================================


class RBACFieldRowProtocol(Protocol):
    """Protocol for rows that support RBAC field purging.

    Row classes used with RBACFieldPurger/RBACFieldBatchPurger must implement this method.
    """

    def field(self) -> FieldRef:
        """Return the FieldRef for RBAC cleanup."""
        ...


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RBACFieldPurger(BasePurger[TRow]):
    """Single-row RBAC field purger by primary key.

    Inherits row_class and pk_value from BasePurger.
    The row_class must implement RBACFieldRowProtocol (field() method).
    """

    pass


@dataclass
class RBACFieldPurgerResult(BasePurgerResult[TRow]):
    """Result of executing a single-row RBAC field purge."""

    pass


class RBACFieldBatchPurgerSpec(BaseBatchPurgerSpec[TRow]):
    """Spec for RBAC field batch purge operations.

    Inherits build_subquery() from BaseBatchPurgerSpec.
    The selected rows must implement RBACFieldRowProtocol.
    """

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


async def _fetch_row_by_pk(
    db_sess: SASession,
    purger: RBACFieldPurger[TRow],
) -> TRow | None:
    """Fetch a row by primary key."""
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    result = await db_sess.scalars(sa.select(row_class).where(pk_columns[0] == purger.pk_value))
    return result.first()


async def _delete_row_by_pk(
    db_sess: SASession,
    purger: RBACFieldPurger[TRow],
) -> None:
    """Delete a row by primary key."""
    row_class = purger.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    await db_sess.execute(sa.delete(table).where(pk_columns[0] == purger.pk_value))


# =============================================================================
# Public API
# =============================================================================


async def execute_rbac_field_purger(
    db_sess: SASession,
    purger: RBACFieldPurger[TRow],
) -> RBACFieldPurgerResult[TRow] | None:
    """
    Execute DELETE for a single field-scoped entity by primary key, along with related RBAC entries.

    The row_class must implement RBACFieldRowProtocol (field() method).

    Operations performed:
    1. Fetch row by primary key to get RBAC info
    2. Delete EntityFieldRow (field-entity mapping)
    3. Delete the main object row

    Args:
        db_sess: Async SQLAlchemy session (must be writable)
        purger: Purger containing row_class and pk_value

    Returns:
        RBACFieldPurgerResult containing the deleted row, or None if no row matched
    """
    # 1. Fetch row to get RBAC info
    row = await _fetch_row_by_pk(db_sess, purger)
    if row is None:
        return None

    # 2. Extract field from row (must implement RBACFieldRowProtocol)
    field: FieldRef = row.field()  # type: ignore[attr-defined]

    # 3. Delete RBAC entries (EntityFieldRow)
    await _delete_entity_field(db_sess, field)

    # 4. Delete main row
    await _delete_row_by_pk(db_sess, purger)

    return RBACFieldPurgerResult(row=row)


async def execute_rbac_field_batch_purger(
    db_sess: SASession,
    purger: RBACFieldBatchPurger[TRow],
) -> RBACFieldBatchPurgerResult:
    """
    Execute batch DELETE for field-scoped entities with RBAC cleanup.

    The selected rows must implement RBACFieldRowProtocol (field() method).

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

    while True:
        # 1. Select batch of rows to delete
        subquery = purger.spec.build_subquery().limit(purger.batch_size)
        rows = list((await db_sess.scalars(subquery)).all())

        if not rows:
            break

        # 2. Extract field_ids from rows (must implement RBACFieldRowProtocol)
        field_ids: list[FieldRef] = [
            row.field()  # type: ignore[attr-defined]
            for row in rows
        ]

        # 3. Clean up RBAC entries for fields
        total_entity_field += await _batch_delete_entity_fields(db_sess, field_ids)

        # 4. Delete main rows
        table = cast(sa.Table, purger.spec.build_subquery().froms[0])
        pk_columns = list(table.primary_key.columns)

        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Batch purger only supports single-column primary keys (table: {table.name})",
            )

        pk_col = pk_columns[0]
        pk_values = [getattr(row, pk_col.key) for row in rows]

        result = await db_sess.execute(sa.delete(table).where(pk_col.in_(pk_values)))
        batch_deleted = cast(CursorResult, result).rowcount or 0
        total_deleted += batch_deleted

        if len(rows) < purger.batch_size:
            break

    return RBACFieldBatchPurgerResult(
        deleted_count=total_deleted,
        deleted_entity_field_count=total_entity_field,
    )
