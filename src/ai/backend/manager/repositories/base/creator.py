"""Creator for repository insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ai.backend.manager.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class CreatorSpec(ABC, Generic[TRow]):
    """Abstract base class defining a row to insert.

    Implementations specify what to create by providing:
    - A build_row() method that returns the ORM instance to insert
    """

    @abstractmethod
    def build_row(self) -> TRow:
        """Build ORM row instance to insert.

        Returns:
            An ORM model instance to be inserted
        """
        raise NotImplementedError


@dataclass
class Creator(Generic[TRow]):
    """Bundles creator spec for insert operations.

    Attributes:
        spec: CreatorSpec implementation defining what to create.

    Note:
        Additional fields (e.g., RBAC context) may be added later.
    """

    spec: CreatorSpec[TRow]


@dataclass
class CreatorResult(Generic[TRow]):
    """Result of executing a create operation."""

    row: TRow


async def execute_creator(
    db_sess: SASession,
    creator: Creator[TRow],
) -> CreatorResult[TRow]:
    """Execute INSERT with creator.

    Args:
        db_sess: Database session (must be writable)
        creator: Creator containing spec for the row to insert

    Returns:
        CreatorResult containing the created row with generated values (id, timestamps, etc.)

    Example:
        class UserCreatorSpec(CreatorSpec[UserRow]):
            def __init__(self, name: str, email: str):
                self._name = name
                self._email = email

            def build_row(self) -> UserRow:
                return UserRow(name=self._name, email=self._email)

        creator = Creator(spec=UserCreatorSpec("Alice", "alice@example.com"))
        result = await execute_creator(db_sess, creator)
        print(result.row.id)  # Generated ID
    """
    row = creator.spec.build_row()
    db_sess.add(row)
    await db_sess.flush()
    # Note: refresh() is not needed - SQLAlchemy 2.0 + asyncpg automatically uses RETURNING
    # to populate server_default values (id, created_at, etc.) after flush()
    return CreatorResult(row=row)


@dataclass
class BulkCreator(Generic[TRow]):
    """Bundles multiple creator specs for bulk insert operations.

    Attributes:
        specs: Sequence of CreatorSpec implementations defining what to create.

    Note:
        Additional fields (e.g., RBAC context) may be added later.
    """

    specs: Sequence[CreatorSpec[TRow]]


@dataclass
class BulkCreatorResult(Generic[TRow]):
    """Result of executing a bulk create operation."""

    rows: list[TRow]


async def execute_bulk_creator(
    db_sess: SASession,
    bulk_creator: BulkCreator[TRow],
) -> BulkCreatorResult[TRow]:
    """Execute bulk INSERT with multiple creator specs.

    Args:
        db_sess: Database session (must be writable)
        bulk_creator: BulkCreator containing specs for rows to insert

    Returns:
        BulkCreatorResult containing all created rows with generated values

    Note:
        All rows are inserted in a single flush operation for efficiency.
        The caller controls the transaction boundary (commit/rollback).
    """
    if not bulk_creator.specs:
        return BulkCreatorResult(rows=[])

    rows = [spec.build_row() for spec in bulk_creator.specs]
    db_sess.add_all(rows)
    await db_sess.flush()
    # Note: refresh() loop removed - SQLAlchemy 2.0 + asyncpg automatically uses RETURNING
    # to populate server_default values (id, created_at, etc.) after flush()
    return BulkCreatorResult(rows=rows)
