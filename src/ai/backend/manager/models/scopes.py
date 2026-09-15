"""Operation-scope abstractions for the models (DB) layer.

``OperationScope`` bounds the rows a DB operation may touch — searches and batch
writes alike — and converts to a
:data:`~ai.backend.manager.models.clauses.QueryCondition`; ``ExistenceCheck``
names an entity whose existence the operation depends on. They live at the models
layer so that repositories/services can build scoped operations without importing
upward into the repositories layer.

What a condition may read depends on the row's shape; see ``KNOWLEDGE.md``.
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
    """An entity a scope names, and the error raised when it does not exist.

    Omitted where authorization has already settled that existence.
    """

    column: sa.orm.attributes.InstrumentedAttribute[T]
    """The column to check (e.g., ResourceGroupRow.name)."""

    value: T
    """The value to check for existence."""

    error: BackendAIError
    """The error to raise if the entity doesn't exist."""


class OperationScope(ABC):
    """Abstract base class for an operation's scope restriction.

    Bounds the rows an operation may touch — a scoped search reads within it, a
    scoped batch write cannot reach past it. It never authorizes: the action's
    scope or bulk check runs first and this narrows what that check allowed.
    """

    @abstractmethod
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition.

        The conditions of several scopes are OR-ed; an empty scope list is rejected
        rather than widened into a read of everything.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        """Return the entities this scope names.

        Every check of every scope is validated in one query before the main query
        runs. Empty where authorization already answered for them.
        """
        raise NotImplementedError
