"""Purger for delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Single-row Purger (by PK)
# =============================================================================


@dataclass
class Purger(Generic[TRow]):
    """Single-row delete by primary key.

    Attributes:
        row_class: ORM class for table access and PK detection.
        pk_value: Primary key value to identify the target row.
    """

    row_class: type[TRow]
    pk_value: UUID | str | int


@dataclass
class PurgerResult(Generic[TRow]):
    """Result of executing a single-row delete operation."""

    row: TRow


async def execute_purger(
    db_sess: SASession,
    purger: Purger[TRow],
) -> PurgerResult[TRow] | None:
    """Execute DELETE for a single row by primary key.

    Args:
        db_sess: Database session (must be writable)
        purger: Purger containing row_class and pk_value

    Returns:
        PurgerResult containing the deleted row, or None if no row matched

    Example:
        purger = Purger(
            row_class=SessionRow,
            pk_value=session_id,
        )
        result = await execute_purger(db_sess, purger)
        if result:
            print(result.row.id)  # Deleted row
    """
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

    deleted_row: TRow = row_class(**dict(row_data._mapping))
    return PurgerResult(row=deleted_row)


# =============================================================================
# Batch Purger (by subquery)
# =============================================================================


class BatchPurgerSpec(ABC, Generic[TRow]):
    """Abstract base class for defining batch purge targets.

    Implementations specify what to delete by providing a subquery
    that selects rows to delete. The table and PK columns are inferred
    from the subquery.
    """

    @abstractmethod
    def build_subquery(self) -> sa.sql.Select[tuple[TRow]]:
        """Build a subquery selecting rows to delete.

        Returns:
            A SELECT statement that returns rows to delete

        Example:
            return sa.select(SessionRow).where(
                SessionRow.status == SessionStatus.TERMINATED
            )
        """
        raise NotImplementedError


@dataclass
class BatchPurger(Generic[TRow]):
    """Bundles batch purger spec and batch configuration for bulk delete operations.

    Attributes:
        spec: BatchPurgerSpec implementation defining what to delete.
        batch_size: Batch size for chunked deletion. Deletes in batches of
            the specified size to avoid long-running transactions.
    """

    spec: BatchPurgerSpec[TRow]
    batch_size: int = 1000


@dataclass
class BatchPurgerResult:
    """Result of executing a batch purge operation."""

    deleted_count: int


async def execute_batch_purger(
    db_sess: SASession,
    purger: BatchPurger[TRow],
) -> BatchPurgerResult:
    """Execute bulk delete with batch purger.

    Args:
        db_sess: Database session (must be writable)
        purger: BatchPurger containing spec and batch configuration

    Returns:
        BatchPurgerResult containing the total count of deleted rows

    Note:
        This performs a hard delete. For soft delete, implement
        in the repository layer using update statements.
        Supports both single-column and composite primary keys.

    Example:
        class OldSessionBatchPurgerSpec(BatchPurgerSpec[SessionRow]):
            def __init__(self, cutoff: datetime):
                self._cutoff = cutoff

            def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
                return (
                    sa.select(SessionRow)
                    .where(SessionRow.status == SessionStatus.TERMINATED)
                    .where(SessionRow.terminated_at < self._cutoff)
                )

        purger = BatchPurger(spec=OldSessionBatchPurgerSpec(cutoff_date))
        result = await execute_batch_purger(db_sess, purger)
    """
    # Extract table and PK columns from the subquery
    base_subquery = purger.spec.build_subquery()
    table = base_subquery.froms[0]
    pk_columns = list(table.primary_key.columns)

    total_deleted = 0

    # Batched delete using subquery with PK tuple matching
    while True:
        sub = purger.spec.build_subquery().subquery()
        # Select PK columns from subquery using column names
        pk_subquery = sa.select(*[sub.c[pk_col.key] for pk_col in pk_columns]).limit(
            purger.batch_size
        )

        # Delete rows matching the subquery (supports composite PKs)
        stmt = sa.delete(table).where(sa.tuple_(*pk_columns).in_(pk_subquery))
        result = await db_sess.execute(stmt)

        batch_deleted = result.rowcount
        total_deleted += batch_deleted

        if batch_deleted < purger.batch_size:
            # No more rows to delete
            break

    return BatchPurgerResult(deleted_count=total_deleted)
