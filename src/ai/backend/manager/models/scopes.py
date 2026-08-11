"""Operation-scope abstractions for the models (DB) layer.

``OperationScope`` bounds the rows a DB operation may touch — searches and batch
writes alike — and converts to a
:data:`~ai.backend.manager.models.clauses.QueryCondition`; ``ExistenceCheck``
validates that required entities exist before the operation runs. They live at
the models layer so that repositories/services can build scoped operations
without importing upward into the repositories layer.
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


class OperationScope(ABC):
    """Abstract base class for an operation's scope restriction.

    Bounds the rows an operation may touch — a scoped search reads within it, a
    scoped batch write cannot reach past it. It converts to a QueryCondition that
    is merged into the operation's statement; existence checks are validated
    first.
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
