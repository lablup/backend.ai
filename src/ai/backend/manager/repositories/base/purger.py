"""Purger for delete operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.types import ConflictCheck

from .integrity import parse_integrity_error

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


# =============================================================================
# Purge Precondition Validation
# =============================================================================


async def validate_conflict_checks(
    db_sess: SASession,
    conflict_checks: Sequence[ConflictCheck],
) -> None:
    """Validate conflict checks in a single query, raising the first failing check's error."""
    if not conflict_checks:
        return

    select_clauses = [
        sa.exists().where(check.condition()).label(f"conflict_{i}")
        for i, check in enumerate(conflict_checks)
    ]
    result = await db_sess.execute(sa.select(*select_clauses))
    row = result.mappings().one()

    for i, check in enumerate(conflict_checks):
        if row[f"conflict_{i}"]:
            raise check.error


# =============================================================================
# Single-row Purger (by PK)
# =============================================================================


class PurgerSpec[TRow: Base](ABC):
    """Abstract base class defining a single-row purge target."""

    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def pk_value(self) -> UUID | str | int:
        """Return the primary key value identifying the target row."""
        raise NotImplementedError

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before deletion (empty if none)."""
        raise NotImplementedError


@dataclass
class Purger[TRow: Base]:
    """Bundles purger spec for single-row delete operations.

    Attributes:
        spec: PurgerSpec implementation defining what to delete.
    """

    spec: PurgerSpec[TRow]


@dataclass
class PurgerResult[TRow: Base]:
    """Result of executing a single-row delete operation."""

    row: TRow


@dataclass
class BulkPurgerError[TRow: Base]:
    """Error information for a failed bulk purge operation.

    Contains the purger that failed and the exception for debugging.
    Follows the BulkCreatorError pattern.

    Attributes:
        purger: The Purger that failed
        exception: The exception that occurred
        index: Original position in purger list for traceability
    """

    purger: Purger[TRow]
    exception: Exception
    index: int


@dataclass
class BulkPurgerResultWithFailures[TRow: Base]:
    """Result of bulk purge operation supporting partial failures.

    Follows the BulkCreatorResultWithFailures pattern with successes and errors.
    Unlike batch purger which fails atomically, this allows some rows
    to succeed while others fail.

    Attributes:
        successes: Successfully deleted rows
        errors: Failed purgers with error information
    """

    successes: list[TRow] = field(default_factory=list)
    errors: list[BulkPurgerError[TRow]] = field(default_factory=list)

    def success_count(self) -> int:
        """Get count of successfully deleted rows."""
        return len(self.successes)

    def has_failures(self) -> bool:
        """Check if any failures occurred."""
        return len(self.errors) > 0


async def execute_purger[TRow: Base](
    db_sess: SASession,
    purger: Purger[TRow],
) -> PurgerResult[TRow] | None:
    """Execute DELETE for a single row by primary key.

    The spec's ``conflict_checks`` are validated in a single query before
    deletion.

    Returns:
        PurgerResult containing the deleted row, or None if no row matched

    Raises:
        BackendAIError: The error declared by the first failing conflict check.
        RepositoryIntegrityError: If the DELETE violates a database constraint
            not covered by ``conflict_checks``.
    """
    spec = purger.spec
    row_class = spec.row_class()
    table = row_class.__table__
    pk_columns = list(table.primary_key.columns)

    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            f"Purger only supports single-column primary keys (table: {table.name})",
        )

    await validate_conflict_checks(db_sess, spec.conflict_checks())

    stmt = sa.delete(table).where(pk_columns[0] == spec.pk_value()).returning(*table.columns)

    try:
        result = await db_sess.execute(stmt)
    except sa.exc.IntegrityError as e:
        raise parse_integrity_error(e) from e
    row_data = result.fetchone()

    if row_data is None:
        return None

    deleted_row: TRow = row_class(**dict(row_data._mapping))
    return PurgerResult(row=deleted_row)


# =============================================================================
# Batch Purger (by subquery)
# =============================================================================


class BatchPurgerSpec[TRow: Base](ABC):
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

    @abstractmethod
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        """Return rows that must not exist before deletion (empty if none)."""
        raise NotImplementedError


@dataclass
class BatchPurger[TRow: Base]:
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


async def execute_bulk_purger_partial[TRow: Base](
    db_sess: SASession,
    purgers: list[Purger[TRow]],
) -> BulkPurgerResultWithFailures[TRow]:
    """Execute bulk DELETE with partial failure support.

    Unlike execute_batch_purger which uses subquery-based deletion and fails
    atomically, this function processes each purger individually and collects
    both successes and failures.

    Processing strategy:
    - Each purger is executed individually within a savepoint (begin_nested)
    - If a purger succeeds, the deleted row is added to successes
    - If a purger fails (any exception), it's added to errors with context
    - If a purger targets a non-existent PK, no row is returned (not an error)
    - Order is preserved in successes list

    Args:
        db_sess: Database session (must be writable)
        purgers: List of Purger instances targeting rows to delete

    Returns:
        BulkPurgerResultWithFailures containing successes and errors

    Raises:
        UnsupportedCompositePrimaryKeyError: If any purger targets a table
            with composite primary key

    Note:
        The caller controls the transaction boundary (commit/rollback).
        Successful deletes are flushed immediately and will persist on commit.
        Failed deletes do not affect successful ones.

    Example:
        purgers = [
            Purger(spec=SessionPurgerSpec(session_id_1)),
            Purger(spec=SessionPurgerSpec(session_id_2)),
            Purger(spec=SessionPurgerSpec(session_id_with_fk_constraint)),  # Fails
        ]
        result = await execute_bulk_purger_partial(db_sess, purgers)

        print(f"Deleted {result.success_count()} sessions")
        print(f"Failed {len(result.errors)} sessions")
        for error in result.errors:
            print(f"  - Index {error.index}: {error.exception}")
    """
    if not purgers:
        return BulkPurgerResultWithFailures(successes=[], errors=[])

    successes: list[TRow] = []
    errors: list[BulkPurgerError[TRow]] = []

    for index, purger in enumerate(purgers):
        # Use nested transaction (savepoint) to isolate each row deletion
        # If this row fails, only this savepoint is rolled back, not the entire session
        try:
            async with db_sess.begin_nested():
                spec = purger.spec
                row_class = spec.row_class()
                table = row_class.__table__
                pk_columns = list(table.primary_key.columns)

                if len(pk_columns) != 1:
                    raise UnsupportedCompositePrimaryKeyError(
                        f"Purger only supports single-column primary keys (table: {table.name})",
                    )

                await validate_conflict_checks(db_sess, spec.conflict_checks())

                stmt = (
                    sa.delete(table)
                    .where(pk_columns[0] == spec.pk_value())
                    .returning(*table.columns)
                )

                result = await db_sess.execute(stmt)
                row_data = result.fetchone()

                # If no row matched, just skip (not an error)
                if row_data is not None:
                    deleted_row: TRow = row_class(**dict(row_data._mapping))
                    successes.append(deleted_row)
        except sa.exc.IntegrityError as e:
            # The nested transaction automatically rolls back on exception
            # This only affects the current row, not previous successful ones
            parsed = parse_integrity_error(e)
            errors.append(
                BulkPurgerError(
                    purger=purger,
                    exception=parsed,
                    index=index,
                )
            )
        except Exception as e:
            # The nested transaction automatically rolls back on exception
            # This only affects the current row, not previous successful ones
            errors.append(
                BulkPurgerError(
                    purger=purger,
                    exception=e,
                    index=index,
                )
            )

    return BulkPurgerResultWithFailures(successes=successes, errors=errors)


async def execute_batch_purger[TRow: Base](
    db_sess: SASession,
    purger: BatchPurger[TRow],
) -> BatchPurgerResult:
    """Execute bulk delete with batch purger.

    The spec's ``conflict_checks`` are validated in a single query before
    deletion starts.

    Args:
        db_sess: Database session (must be writable)
        purger: BatchPurger containing spec and batch configuration

    Returns:
        BatchPurgerResult containing the total count of deleted rows

    Raises:
        BackendAIError: The error declared by the first failing conflict check.
        RepositoryIntegrityError: If the DELETE violates a database constraint
            (e.g., foreign key) not covered by the spec's ``conflict_checks``.

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
    # Resolve the target table from the mapped entity rather than the query's
    # FROM clause: an entity with an eager (``lazy="joined"``) relationship
    # compiles to an _ORMJoin whose primary_key is a ColumnSet, not a Table.
    base_subquery = purger.spec.build_subquery()
    entity = base_subquery.column_descriptions[0]["entity"]
    table = sa.inspect(entity).local_table
    pk_columns = list(table.primary_key.columns)

    await validate_conflict_checks(db_sess, purger.spec.conflict_checks())

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
        try:
            result = await db_sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            raise parse_integrity_error(e) from e

        batch_deleted = cast(CursorResult[Any], result).rowcount
        total_deleted += batch_deleted

        if batch_deleted < purger.batch_size:
            # No more rows to delete
            break

    return BatchPurgerResult(deleted_count=total_deleted)
