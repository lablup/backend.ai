"""Search-scope abstractions for the models (DB) layer.

``SearchScope`` defines the parameters of an entity-based search query and
converts to a :data:`~ai.backend.manager.models.clauses.QueryCondition`;
``ExistenceCheck`` validates that required entities exist before the query runs.
They live at the models layer so that repositories/services can build scoped
queries without importing upward into the repositories layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.models.clauses import QueryCondition


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
