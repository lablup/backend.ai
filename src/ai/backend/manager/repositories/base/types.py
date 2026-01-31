"""Type definitions for repository layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

# QueryCondition now returns a ColumnElement (whereclause) instead of modifying stmt
type QueryCondition = Callable[[], sa.sql.expression.ColumnElement[bool]]

T = TypeVar("T")


@dataclass(frozen=True)
class ExistenceCheck[T]:
    """Defines an existence check for scope validation.

    Used to validate that required entities exist before executing a query.
    Multiple checks are combined into a single query for efficiency.
    """

    column: sa.orm.attributes.InstrumentedAttribute[T]
    """The column to check (e.g., ScalingGroupRow.name)."""

    value: T
    """The value to check for existence."""

    error: BackendAIError
    """The error to raise if the entity doesn't exist."""


class SearchScope(ABC):
    """Abstract base class for search scope.

    Scope defines required parameters for entity-based search queries.
    It converts to a QueryCondition that can be added to BatchQuerier conditions.
    Optionally defines existence checks for validation.
    """

    @abstractmethod
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition."""
        raise NotImplementedError

    @property
    @abstractmethod
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        """Return existence checks for scope validation.

        All checks are validated in a single query before the main query executes.
        """
        raise NotImplementedError


type QueryOrder = sa.sql.expression.UnaryExpression[Any] | sa.sql.expression.ColumnElement[Any]

# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row[Any]")
