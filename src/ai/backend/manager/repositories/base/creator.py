"""Creator for repository insert operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition

from .integrity import match_integrity_error, parse_integrity_error
from .querier import ExistsQuerier
from .types import IntegrityErrorCheck

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession
    from sqlalchemy.orm import InstrumentedAttribute

TRow = TypeVar("TRow", bound=Base)


class CreatorSpec[TRow: Base](ABC):
    """Abstract base class defining a row to insert.

    Implementations specify what to create by providing:
    - A build_row() method that returns the ORM instance to insert
    """

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Integrity error checks to match after flush.

        Override to declare expected constraint violations and their domain errors.
        Empty by default (unmatched errors raise RepositoryIntegrityError).
        """
        return ()

    @abstractmethod
    def build_row(self) -> TRow:
        """Build ORM row instance to insert.

        Returns:
            An ORM model instance to be inserted
        """
        raise NotImplementedError


class DependentCreatorSpec[TDependency, TRow: Base](ABC):
    """Abstract base class defining a row whose construction depends on a resolved value.

    Unlike CreatorSpec, ``build_row`` receives a dependency value (e.g. a parent row's
    generated id) that is only known at execution time. The caller (repository) builds
    the dependency from a prior operation's result and passes it in. Each spec still
    owns exactly one table's row.
    """

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """Integrity error checks to match after flush.

        Override to declare expected constraint violations and their domain errors.
        Empty by default (unmatched errors raise RepositoryIntegrityError).
        """
        return ()

    @abstractmethod
    def build_row(self, dependency: TDependency) -> TRow:
        """Build ORM row instance to insert, using the resolved dependency value.

        Args:
            dependency: Value resolved from a prior operation (e.g. a parent id).

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
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, creator.spec.integrity_error_checks)
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
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        # Use first spec's checks (all specs share the same CreatorSpec subclass)
        checks = bulk_creator.specs[0].integrity_error_checks
        match_integrity_error(parsed, checks)
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
            except sa.exc.IntegrityError as e:
                parsed = parse_integrity_error(e)
                checks = spec.integrity_error_checks
                if checks:
                    try:
                        match_integrity_error(parsed, checks)
                    except Exception as domain_error:
                        errors.append(
                            BulkCreatorError(spec=spec, exception=domain_error, index=index)
                        )
                else:
                    errors.append(BulkCreatorError(spec=spec, exception=parsed, index=index))
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


@dataclass
class ConditionalCreator[TRow: Base, TGateRow: Base]:
    """A creator spec paired with the existence gate (``only_if``) that authorizes it.

    The gate is checked (``SELECT EXISTS``) inside the same write transaction as the insert,
    so the authorization and the write commit atomically — no check-then-write race. One item
    of a :class:`BulkConditionalCreator`.

    Attributes:
        spec: What to insert.
        only_if: Existence check that must hold for the insert to proceed.
    """

    spec: CreatorSpec[TRow]
    only_if: ExistsQuerier[TGateRow]


@dataclass
class BulkConditionalCreator[TRow: Base, TGateRow: Base]:
    """Bundles gated creator specs for a partial-success conditional bulk insert.

    Each item carries its own ``only_if`` gate and runs in its own savepoint: a rejected gate
    (or a failed insert) is reported as a per-item failure and skips only that item, while the
    rest proceed. See ``WriteOps.bulk_conditional_create_partial``.

    Attributes:
        specs: Gated creator specs to insert, each independently.
    """

    specs: Sequence[ConditionalCreator[TRow, TGateRow]]


async def execute_dependent_creator[TDependency, TRow: Base](
    db_sess: SASession,
    spec: DependentCreatorSpec[TDependency, TRow],
    dependency: TDependency,
) -> CreatorResult[TRow]:
    """Execute INSERT for a single dependent spec with a resolved dependency.

    The caller builds ``dependency`` from a prior operation's result (e.g. a parent id)
    and passes it in; the spec's build_row receives it.

    Args:
        db_sess: Database session (must be writable)
        spec: Dependent creator spec to insert
        dependency: The resolved dependency value passed to the spec's build_row

    Returns:
        CreatorResult containing the created row with generated values

    Note:
        The caller controls the transaction boundary (commit/rollback).
    """
    row = spec.build_row(dependency)
    db_sess.add(row)
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, spec.integrity_error_checks)
    return CreatorResult(row=row)


async def execute_bulk_dependent_creator[TDependency, TRow: Base](
    db_sess: SASession,
    specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
    dependency: TDependency,
) -> BulkCreatorResult[TRow]:
    """Execute bulk INSERT for dependent specs sharing one resolved dependency.

    Each spec builds its row from the same dependency value (e.g. a parent id resolved
    by the caller after creating the parent). All rows are inserted in a single flush.

    Args:
        db_sess: Database session (must be writable)
        specs: Dependent creator specs to insert
        dependency: The resolved dependency value passed to every spec's build_row

    Returns:
        BulkCreatorResult containing all created rows with generated values

    Note:
        The caller controls the transaction boundary (commit/rollback).
    """
    if not specs:
        return BulkCreatorResult(rows=[])

    rows = [spec.build_row(dependency) for spec in specs]
    db_sess.add_all(rows)
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        # Use first spec's checks (all specs share the same DependentCreatorSpec subclass)
        checks = specs[0].integrity_error_checks
        match_integrity_error(parsed, checks)
    return BulkCreatorResult(rows=rows)


@dataclass(frozen=True)
class NextValuePolicy:
    """Describes how to compute the next monotonic value for a column within a scope.

    Used by execute_next_value_creator to assign a sequential value (e.g. a display
    rank) race-free inside a single write transaction.

    Attributes:
        column: The integer column whose next value is computed (e.g. Row.rank).
        scope_condition: WHERE clause limiting the MAX aggregation to a scope.
        lock_selector: SELECT for the parent row to lock with FOR UPDATE, serializing
            concurrent inserts within the same scope. The scope is assumed to have at
            least one lockable parent row.
        gap: Increment added to the current MAX (and the value used when the scope is empty).
    """

    column: InstrumentedAttribute[int]
    scope_condition: QueryCondition
    lock_selector: sa.sql.Select[Any]
    gap: int


async def execute_next_value_creator[TRow: Base](
    db_sess: SASession,
    policy: NextValuePolicy,
    spec: DependentCreatorSpec[int, TRow],
) -> CreatorResult[TRow]:
    """Insert a row with the next monotonic column value, race-free.

    Locks the parent row (FOR UPDATE), reads MAX(column) within the scope, computes the
    next value, and inserts via the dependent spec — all in the caller's single
    transaction. The caller MUST run this inside ``write_ops()`` so the lock and insert
    commit together.

    Args:
        db_sess: Database session (must be writable)
        policy: How to compute the next value (column, scope, parent lock, gap)
        spec: Dependent creator spec whose build_row receives the computed next value

    Returns:
        CreatorResult containing the created row
    """
    await db_sess.execute(policy.lock_selector.with_for_update())
    max_result = await db_sess.execute(
        sa.select(sa.func.max(policy.column)).where(policy.scope_condition())
    )
    max_value = max_result.scalar_one_or_none()
    next_value = (max_value + policy.gap) if max_value is not None else policy.gap

    row = spec.build_row(next_value)
    db_sess.add(row)
    try:
        await db_sess.flush()
    except sa.exc.IntegrityError as e:
        parsed = parse_integrity_error(e)
        match_integrity_error(parsed, spec.integrity_error_checks)
    return CreatorResult(row=row)
