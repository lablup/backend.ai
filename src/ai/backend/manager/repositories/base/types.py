"""Type definitions for repository layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.models.clauses import QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

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


# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row[Any]")


@dataclass(frozen=True)
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

    successes: dict[EntityID, TData]
    errors: dict[EntityID, Exception]
