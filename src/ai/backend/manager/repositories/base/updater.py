"""Updater for repository update operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base

from .integrity import match_integrity_error, parse_integrity_error
from .types import IntegrityErrorCheck, QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class UpdaterSpec[TRow: Base](ABC):
    """Abstract base class defining values to update for single-row updates.

    Implementations specify what to update by providing:
    - row_class property for target table and PK detection
    - build_values() for column-value mapping

    Optional hooks for declarative pre/postconditions:
    - guard_condition(): an extra WHERE predicate AND-merged into the UPDATE
    - not_found_error(): domain error raised when no row matches the PK
    - on_guard_failure(): domain error raised when the row exists but the guard rejects
    """

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build column name to value mapping for update.

        Note: This method should only be called internally by execute_updater
        or apply_to_row. External code should use apply_to_row() instead.

        Returns:
            Dict mapping column names to values
        """
        raise NotImplementedError

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Return integrity error checks for declarative error matching.

        Override in subclasses to map constraint violations to domain errors.
        Default returns empty sequence (no checks, fallback behavior).
        """
        return ()

    @abstractmethod
    def guard_condition(self) -> QueryCondition | None:
        """Optional precondition AND-merged into the WHERE clause.

        Implementations return ``None`` when there is no extra guard.
        """
        raise NotImplementedError

    @abstractmethod
    def not_found_error(self) -> BackendAIError | None:
        """Error raised by the executor when no row matches the primary key.

        Implementations return ``None`` to preserve the historical behaviour
        of returning ``None`` from ``execute_updater`` on a missing row.
        """
        raise NotImplementedError

    @abstractmethod
    def on_guard_failure(self) -> BackendAIError | None:
        """Error raised when the row exists but the guard rejects the update.

        Implementations return ``None`` to make the executor return the
        existing row data unchanged instead of raising.
        """
        raise NotImplementedError

    def apply_to_row(self, row: TRow) -> None:
        """Apply update values to a row object via setattr.

        This method encapsulates the build_values() call and applies
        updates to the row without exposing the internal dict structure.

        Args:
            row: The ORM row object to apply updates to
        """
        for col, value in self.build_values().items():
            setattr(row, col, value)


class BatchUpdaterSpec[TRow: Base](ABC):
    """Abstract base class defining values to update for batch updates.

    Implementations specify what to update by providing:
    - row_class property for target table access
    - build_values() for column-value mapping
    - guard_condition() (optional) for an extra WHERE predicate
    """

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build column name to value mapping for update.

        Returns:
            Dict mapping column names to values
        """
        raise NotImplementedError

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Return integrity error checks for declarative error matching.

        Override in subclasses to map constraint violations to domain errors.
        Default returns empty sequence (no checks, fallback behavior).
        """
        return ()

    @abstractmethod
    def guard_condition(self) -> QueryCondition | None:
        """Optional precondition AND-merged into the WHERE clause.

        Implementations return ``None`` when there is no extra guard.
        """
        raise NotImplementedError


@dataclass
class Updater[TRow: Base]:
    """Bundles updater spec with target info for single-row update operations.

    Attributes:
        spec: UpdaterSpec implementation defining row_class and values to update.
        pk_value: Primary key value to identify the target row.
    """

    spec: UpdaterSpec[TRow]
    pk_value: UUID | str | int


@dataclass
class BatchUpdater[TRow: Base]:
    """Bundles batch updater spec with conditions for batch update operations.

    Attributes:
        spec: BatchUpdaterSpec implementation defining row_class and values to update.
        conditions: List of QueryCondition factories for WHERE clause (AND combined).
    """

    spec: BatchUpdaterSpec[TRow]
    conditions: list[QueryCondition]


@dataclass
class BulkUpdater[TRow: Base]:
    """Bundles multiple updaters for partial-success bulk update operations.

    Attributes:
        updaters: Sequence of single-row Updater instances; each is executed
            inside its own savepoint by ``execute_bulk_updater_partial``.
    """

    updaters: Sequence[Updater[TRow]]


@dataclass
class UpdaterResult[TRow: Base]:
    """Result of executing a single-row update operation."""

    row: TRow


@dataclass
class BatchUpdaterResult:
    """Result of executing a batch update operation."""

    updated_count: int


@dataclass
class BulkUpdaterError[TRow: Base]:
    """Error information for a failed bulk update operation.

    Contains the spec that failed and the exception for debugging.
    Follows the same pattern as BulkCreatorError.

    Attributes:
        spec: The UpdaterSpec that failed
        exception: The exception that occurred
        index: Original position in specs list for traceability
    """

    spec: UpdaterSpec[TRow]
    exception: Exception
    index: int


@dataclass
class BulkUpdaterPartialResult[TRow: Base]:
    """Result of a bulk update operation supporting partial failures.

    Mirrors the BulkCreatorResultWithFailures pattern: each updater runs
    in its own savepoint so failures are isolated and the enclosing
    transaction stays alive.
    """

    successes: list[TRow] = field(default_factory=list)
    errors: list[BulkUpdaterError[TRow]] = field(default_factory=list)

    def success_count(self) -> int:
        return len(self.successes)

    def has_failures(self) -> bool:
        return bool(self.errors)


async def execute_updater[TRow: Base](
    db_sess: SASession,
    updater: Updater[TRow],
) -> UpdaterResult[TRow] | None:
    """Execute UPDATE for a single row by primary key.

    The base WHERE clause is ``pk = :pk``; if the spec defines
    ``guard_condition()``, that predicate is AND-merged in.

    Behaviour when the UPDATE affects zero rows:
    - Re-query the row by primary key.
    - Not present: raise ``spec.not_found_error()`` if defined, else return ``None``
      (existing behaviour preserved).
    - Present (guard rejected): raise ``spec.on_guard_failure()`` if defined, else
      return ``UpdaterResult(row=existing)``.

    Args:
        db_sess: Database session (must be writable)
        updater: Updater containing spec and pk_value

    Returns:
        ``UpdaterResult`` with the updated row (or the existing row when there are no
        values to update or the guard rejected). ``None`` only when the row does not
        exist and the spec does not declare a ``not_found_error``.
    """
    spec = updater.spec
    row_class = spec.row_class
    table = row_class.__table__
    pk_columns = list(table.primary_key.columns)
    if len(pk_columns) != 1:
        raise UnsupportedCompositePrimaryKeyError(
            "Updater only supports single-column primary keys",
        )
    pk_col = pk_columns[0]
    values = spec.build_values()
    guard = spec.guard_condition()

    if not values:
        # No columns to update: return the current row if it exists so callers can tell
        # "nothing to change" apart from "row not found".
        existing = await db_sess.execute(sa.select(row_class).where(pk_col == updater.pk_value))
        current_row = existing.scalar_one_or_none()
        if current_row is None:
            not_found = spec.not_found_error()
            if not_found is not None:
                raise not_found
            return None
        return UpdaterResult(row=current_row)

    where_conditions: list[sa.sql.expression.ColumnElement[bool]] = [pk_col == updater.pk_value]
    if guard is not None:
        where_conditions.append(guard())

    update_stmt = (
        sa.update(table).values(values).where(sa.and_(*where_conditions)).returning(*table.columns)
    )
    select_stmt = sa.select(row_class).from_statement(update_stmt)
    try:
        result = await db_sess.execute(select_stmt)
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, spec.integrity_error_checks)
    updated_row = result.scalar_one_or_none()
    if updated_row is not None:
        return UpdaterResult(row=updated_row)

    # Zero rows updated — distinguish missing row from guard rejection.
    check = await db_sess.execute(sa.select(row_class).where(pk_col == updater.pk_value))
    existing_row = check.scalar_one_or_none()
    if existing_row is None:
        not_found = spec.not_found_error()
        if not_found is not None:
            raise not_found
        return None
    guard_failure = spec.on_guard_failure()
    if guard_failure is not None:
        raise guard_failure
    return UpdaterResult(row=existing_row)


async def execute_batch_updater[TRow: Base](
    db_sess: SASession,
    updater: BatchUpdater[TRow],
) -> BatchUpdaterResult:
    """Execute UPDATE with multiple conditions (AND combined).

    The WHERE clause is the AND of ``updater.conditions`` and, when defined,
    ``updater.spec.guard_condition()``.

    Args:
        db_sess: Database session (must be writable)
        updater: BatchUpdater containing spec and conditions for the batch update

    Returns:
        BatchUpdaterResult with count of updated rows
    """
    spec = updater.spec
    row_class = spec.row_class
    table = row_class.__table__
    values = spec.build_values()

    stmt = sa.update(table).values(values)
    for condition in updater.conditions:
        stmt = stmt.where(condition())
    guard = spec.guard_condition()
    if guard is not None:
        stmt = stmt.where(guard())

    try:
        result = await db_sess.execute(stmt)
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, spec.integrity_error_checks)
    return BatchUpdaterResult(updated_count=cast(CursorResult[Any], result).rowcount)


async def execute_bulk_updater_partial[TRow: Base](
    db_sess: SASession,
    bulk: BulkUpdater[TRow],
) -> BulkUpdaterPartialResult[TRow]:
    """Execute each updater in its own savepoint, collecting successes and failures.

    Mirrors ``execute_bulk_creator_partial``: a failure in one updater (integrity
    violation, guard error, missing row error) is recorded against that updater
    and does not abort the enclosing transaction.
    """
    partial: BulkUpdaterPartialResult[TRow] = BulkUpdaterPartialResult()
    for index, updater in enumerate(bulk.updaters):
        try:
            async with db_sess.begin_nested():
                result = await execute_updater(db_sess, updater)
                if result is not None:
                    partial.successes.append(result.row)
        except Exception as exc:
            partial.errors.append(BulkUpdaterError(spec=updater.spec, exception=exc, index=index))
    return partial
