"""Updater for repository update operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.base import Base

from .types import QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class UpdaterSpec(ABC, Generic[TRow]):
    """Abstract base class defining values to update for single-row updates.

    Implementations specify what to update by providing:
    - row_class property for target table and PK detection
    - build_values() for column-value mapping
    """

    @property
    @abstractmethod
    def row_class(self) -> type[TRow]:
        """Return the ORM class for table access and PK detection."""
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build column name to value mapping for update.

        Returns:
            Dict mapping column names to values
        """
        raise NotImplementedError


class BatchUpdaterSpec(ABC, Generic[TRow]):
    """Abstract base class defining values to update for batch updates.

    Implementations specify what to update by providing:
    - row_class property for target table access
    - build_values() for column-value mapping
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


@dataclass
class Updater(Generic[TRow]):
    """Bundles updater spec with target info for single-row update operations.

    Attributes:
        spec: UpdaterSpec implementation defining row_class and values to update.
        pk_value: Primary key value to identify the target row.
    """

    spec: UpdaterSpec[TRow]
    pk_value: UUID | str | int


@dataclass
class BatchUpdater(Generic[TRow]):
    """Bundles batch updater spec with conditions for batch update operations.

    Attributes:
        spec: BatchUpdaterSpec implementation defining row_class and values to update.
        conditions: List of QueryCondition factories for WHERE clause (AND combined).
    """

    spec: BatchUpdaterSpec[TRow]
    conditions: list[QueryCondition]


@dataclass
class UpdaterResult(Generic[TRow]):
    """Result of executing a single-row update operation."""

    row: TRow


@dataclass
class BatchUpdaterResult:
    """Result of executing a batch update operation."""

    updated_count: int


async def execute_updater(
    db_sess: SASession,
    updater: Updater[TRow],
) -> UpdaterResult[TRow] | None:
    """Execute UPDATE for a single row by primary key.

    Args:
        db_sess: Database session (must be writable)
        updater: Updater containing spec and pk_value

    Returns:
        UpdaterResult containing the updated row, or None if no row matched

    Example:
        class SessionStatusUpdaterSpec(UpdaterSpec[SessionRow]):
            def __init__(self, new_status: str):
                self._new_status = new_status

            @property
            def row_class(self) -> type[SessionRow]:
                return SessionRow

            def build_values(self) -> dict[str, Any]:
                return {"status": self._new_status}

        updater = Updater(
            spec=SessionStatusUpdaterSpec("terminated"),
            pk_value=session_id,
        )
        result = await execute_updater(db_sess, updater)
        if result:
            print(result.row.status)  # "terminated"
    """
    row_class = updater.spec.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    pk_columns = list(table.primary_key.columns)
    values = updater.spec.build_values()

    if len(pk_columns) != 1:
        raise ValueError("Updater only supports single-column primary keys")

    stmt = (
        sa.update(table)
        .values(values)
        .where(pk_columns[0] == updater.pk_value)
        .returning(*table.columns)
    )

    result = await db_sess.execute(stmt)
    row_data = result.fetchone()

    if row_data is None:
        return None

    updated_row: TRow = row_class(**dict(row_data._mapping))
    return UpdaterResult(row=updated_row)


async def execute_batch_updater(
    db_sess: SASession,
    updater: BatchUpdater[TRow],
) -> BatchUpdaterResult:
    """Execute UPDATE with multiple conditions (AND combined).

    Args:
        db_sess: Database session (must be writable)
        updater: BatchUpdater containing spec and conditions for the batch update

    Returns:
        BatchUpdaterResult with count of updated rows

    Example:
        class ItemStatusBatchUpdaterSpec(BatchUpdaterSpec[ItemRow]):
            def __init__(self, new_status: str):
                self._new_status = new_status

            @property
            def row_class(self) -> type[ItemRow]:
                return ItemRow

            def build_values(self) -> dict[str, Any]:
                return {"status": self._new_status}

        updater = BatchUpdater(
            spec=ItemStatusBatchUpdaterSpec("processed"),
            conditions=[lambda: ItemRow.__table__.c.status == "pending"],
        )
        result = await execute_batch_updater(db_sess, updater)
        print(result.updated_count)  # N
    """
    spec = updater.spec
    row_class = spec.row_class
    table = row_class.__table__  # type: ignore[attr-defined]
    values = spec.build_values()

    stmt = sa.update(table).values(values)
    for condition in updater.conditions:
        stmt = stmt.where(condition())

    result = await db_sess.execute(stmt)
    return BatchUpdaterResult(updated_count=result.rowcount)
