"""Type definitions for repository layer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.common.exception import BackendAIError
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
