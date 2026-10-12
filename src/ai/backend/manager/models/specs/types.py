"""Shared declarations of the v2 lineage: the checks write specs carry, and the
result shapes the ops execution answers with."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.models.clauses import QueryCondition

if TYPE_CHECKING:
    from ai.backend.manager.errors.repository import RepositoryIntegrityError


@dataclass(frozen=True)
class ConflictCheck:
    """Defines a conflict check for destructive-operation validation.

    The inverse of ExistenceCheck: validates that no row matching the condition
    exists before executing a destructive operation (e.g. purge).
    Multiple checks are combined into a single query for efficiency.
    """

    condition: QueryCondition
    """Condition selecting conflicting rows (e.g., lambda: UserRow.domain_name == name)."""

    error: BackendAIError
    """The error to raise if any conflicting row exists."""


@dataclass(frozen=True)
class GuardCheck:
    """A condition the named row must satisfy for an updater or a purger to write it.

    Rides on the statement, so no read stands between the check and the write. A row
    failing it is left alone and the write answers with the error declared here.
    Unlike :class:`ConflictCheck`, this names the row already picked, not other rows.
    """

    condition: QueryCondition
    """Condition on the named row (e.g., lambda: RoleRow.source == RoleSource.CUSTOM)."""

    error: BackendAIError
    """The error to raise when the row does not satisfy the condition."""


@dataclass(frozen=True)
class PreconditionCheck:
    """A state elsewhere that forbids the write, declared beside the spec that makes it.

    The database answers some of these through its own constraints, which
    :class:`IntegrityErrorCheck` maps back to a domain error. This is for the ones it
    cannot state: a row in another table that makes the write wrong rather than
    impossible. What to look for is declared here and run by the ops that writes, so
    the spec stays a value.

    Unlike the :class:`GuardCheck` an updater or a purger carries, this is not a
    condition the named row must satisfy: it names rows whose presence turns the write
    away.
    """

    finder: sa.Select[Any]
    """Selects the rows whose presence turns the write away."""

    error: BackendAIError
    """The domain error to raise when one is found."""


@dataclass
class IntegrityErrorCheck:
    """Defines an integrity error check for declarative error matching.

    Used to match parsed integrity errors against expected constraint violations
    and raise domain-specific errors.
    """

    violation_type: type[RepositoryIntegrityError]
    """The integrity error subclass to match (e.g., UniqueConstraintViolationError)."""

    error: BackendAIError
    """The domain error to raise when matched."""

    constraint_name: str | None = None
    """Optional constraint name filter. If None, matches any constraint of the given type."""


@dataclass
class BulkResultWithFailures[TData]:
    """What a bulk write did to each entity the caller named.

    Named as the atomic bulk results are, minus a spec name it cannot carry — one type
    serves both the updater and the purger — leaving the part a caller has to know:
    some of these may have failed while the rest went through.

    Keyed by entity rather than positional: the bulk shape answers per entity, and an
    answer attached to the wrong one is worse than no answer.

    Ordering is per group, not the caller's. A caller that needs its own order re-reads
    these by the ids it passed in.

    Names its fields as the other bulk results do, so a caller reading ``successes`` and
    ``errors`` off this reads them the same way off ``BulkUpdaterResult``.
    """

    successes: dict[EntityIdentifier, TData]
    errors: dict[EntityIdentifier, Exception]


@dataclass
class EntityWithFieldsResult[TData, TFieldData]:
    """An entity and the field rows created under it in the same transaction.

    A dataclass rather than a pair: the two halves are not interchangeable, and a
    caller reading positionally would eventually read them the wrong way round.
    """

    data: TData
    fields: list[TFieldData]
