"""Creator for repository insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

from ai.backend.manager.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

TRow = TypeVar("TRow", bound=Base)


class CreatorSpec[TRow: Base](ABC):
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
class Creator[TRow: Base]:
    """Bundles creator spec for insert operations.

    Attributes:
        spec: CreatorSpec implementation defining what to create.

    Note:
        Additional fields (e.g., RBAC context) may be added later.
    """

    spec: CreatorSpec[TRow]


@dataclass
class CreatorResult[TRow: Base]:
    """Result of executing a create operation."""

    row: TRow


@dataclass
class BulkCreatorError[TRow: Base]:
    """Error information for a failed bulk create operation.

    Contains the spec that failed and the exception for debugging.
    Follows the SessionExecutionResult pattern from scheduler coordinator.

    Attributes:
        spec: The CreatorSpec that failed
        exception: The exception that occurred
        index: Original position in specs list for traceability
    """

    spec: CreatorSpec[TRow]
    exception: Exception
    index: int


@dataclass
class BulkCreatorResultWithFailures[TRow: Base]:
    """Result of bulk create operation supporting partial failures.

    Follows the SessionExecutionResult pattern with successes and errors.
    Unlike BulkCreatorResult which fails atomically, this allows some rows
    to succeed while others fail.

    Attributes:
        successes: Successfully created rows with generated IDs
        errors: Failed specs with error information
    """

    successes: list[TRow] = field(default_factory=list)
    errors: list[BulkCreatorError[TRow]] = field(default_factory=list)

    def success_count(self) -> int:
        """Get count of successfully created rows."""
        return len(self.successes)

    def has_failures(self) -> bool:
        """Check if any failures occurred."""
        return len(self.errors) > 0


async def execute_creator[TRow: Base](
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
class BulkCreator[TRow: Base]:
    """Bundles multiple creator specs for bulk insert operations.

    Attributes:
        specs: Sequence of CreatorSpec implementations defining what to create.

    Note:
        Additional fields (e.g., RBAC context) may be added later.
    """

    specs: Sequence[CreatorSpec[TRow]]


@dataclass
class BulkCreatorResult[TRow: Base]:
    """Result of executing a bulk create operation."""

    rows: list[TRow]


async def execute_bulk_creator[TRow: Base](
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


async def execute_bulk_creator_partial[TRow: Base](
    db_sess: SASession,
    bulk_creator: BulkCreator[TRow],
) -> BulkCreatorResultWithFailures[TRow]:
    """Execute bulk INSERT with partial failure support.

    Unlike execute_bulk_creator which fails atomically, this function
    processes each spec individually and collects both successes and failures.

    Processing strategy:
    - Each spec is built and flushed individually
    - If a spec succeeds, the row is added to successes
    - If a spec fails (any exception), it's added to errors with context
    - Order is preserved in successes list

    Args:
        db_sess: Database session (must be writable)
        bulk_creator: BulkCreator containing specs for rows to insert

    Returns:
        BulkCreatorResultWithFailures containing successes and errors

    Note:
        The caller controls the transaction boundary (commit/rollback).
        Successful rows are flushed immediately and will persist on commit.
        Failed rows do not affect successful ones.

    Example:
        specs = [
            UserCreatorSpec("alice@example.com"),
            UserCreatorSpec("bob@example.com"),
            UserCreatorSpec("invalid-email"),  # Fails validation
        ]
        bulk_creator = BulkCreator(specs=specs)
        result = await execute_bulk_creator_partial(db_sess, bulk_creator)

        print(f"Created {result.success_count()} users")
        print(f"Failed {len(result.errors)} users")
        for error in result.errors:
            print(f"  - Index {error.index}: {error.exception}")
    """
    if not bulk_creator.specs:
        return BulkCreatorResultWithFailures(successes=[], errors=[])

    successes: list[TRow] = []
    errors: list[BulkCreatorError[TRow]] = []

    for index, spec in enumerate(bulk_creator.specs):
        # Use nested transaction (savepoint) to isolate each row insertion
        # If this row fails, only this savepoint is rolled back, not the entire session
        async with db_sess.begin_nested():
            try:
                row = spec.build_row()
                db_sess.add(row)
                await db_sess.flush()
                # SQLAlchemy 2.0 + asyncpg uses RETURNING to populate server_default values
                successes.append(row)
            except Exception as e:
                # The nested transaction automatically rolls back on exception
                # This only affects the current row, not previous successful ones
                errors.append(
                    BulkCreatorError(
                        spec=spec,
                        exception=e,
                        index=index,
                    )
                )

    return BulkCreatorResultWithFailures(successes=successes, errors=errors)
