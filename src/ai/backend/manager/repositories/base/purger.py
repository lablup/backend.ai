"""Purger for bulk delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class PurgeTarget(ABC):
    """Abstract base class for defining purge targets.

    Implementations specify what to delete by providing:
    - The primary key column for the target table
    - A subquery that selects PKs of rows to delete
    """

    @property
    @abstractmethod
    def pk_column(self) -> sa.Column:
        """The primary key column of the target table."""
        raise NotImplementedError

    @abstractmethod
    def build_subquery(self) -> sa.sql.Select:
        """Build a subquery selecting PKs of rows to delete.

        Returns:
            A SELECT statement that returns PK values to delete
        """
        raise NotImplementedError


@dataclass
class Purger:
    """Bundles purge target and batch configuration for bulk delete operations.

    Attributes:
        target: PurgeTarget implementation defining what to delete.
        batch_size: Batch size for chunked deletion. Deletes in batches of
            the specified size to avoid long-running transactions.
    """

    target: PurgeTarget
    batch_size: int = 1000


@dataclass
class PurgerResult:
    """Result of executing a purge operation."""

    deleted_count: int


async def execute_purger(
    db_sess: SASession,
    purger: Purger,
) -> PurgerResult:
    """Execute bulk delete with purger.

    Args:
        db_sess: Database session (must be writable)
        purger: Purger containing target and batch configuration

    Returns:
        PurgerResult containing the total count of deleted rows

    Note:
        This performs a hard delete. For soft delete, implement
        in the repository layer using update statements.

    Example:
        class OldSessionPurgeTarget(PurgeTarget):
            def __init__(self, cutoff: datetime):
                self._cutoff = cutoff

            @property
            def pk_column(self) -> sa.Column:
                return SessionRow.id

            def build_subquery(self) -> sa.sql.Select:
                return (
                    sa.select(SessionRow.id)
                    .where(SessionRow.status == SessionStatus.TERMINATED)
                    .where(SessionRow.terminated_at < self._cutoff)
                )

        purger = Purger(target=OldSessionPurgeTarget(cutoff_date))
        result = await execute_purger(db_sess, purger)
    """
    pk_column = purger.target.pk_column
    table = pk_column.table

    total_deleted = 0

    # Batched delete using subquery
    while True:
        subquery = purger.target.build_subquery().limit(purger.batch_size)

        # Delete rows matching the subquery
        stmt = sa.delete(table).where(pk_column.in_(subquery))
        result = await db_sess.execute(stmt)

        batch_deleted = result.rowcount
        total_deleted += batch_deleted

        if batch_deleted < purger.batch_size:
            # No more rows to delete
            break

    return PurgerResult(deleted_count=total_deleted)
