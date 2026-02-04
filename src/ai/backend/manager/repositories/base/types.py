"""Type definitions for repository layer."""

from __future__ import annotations

from uuid import UUID
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.data.permission.id import ScopeId, ObjectId
from ai.backend.manager.data.permission.types import OperationType, EntityType

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


class ActionScope(ABC):
    """Abstract base class for search scope.

    Scope defines required parameters for entity-based search queries.
    Defines existence checks for validation.
    """

    @property
    @abstractmethod
    def existence_checks(self) -> list[ExistenceCheck]:
        """Return existence checks for scope validation.

        All checks are validated in a single query before the main query executes.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def target(self) -> ScopeId:
        """
        Return the target ScopeId for the scope."""
        raise NotImplementedError

    @property
    @abstractmethod
    def prerequisite_scopes(self) -> set[ScopeId]:
        """
        Return additional target ScopeIds for the scope."""
        raise NotImplementedError


class SearchScope(ActionScope):
    """Abstract base class for search scope.

    Scope defines required parameters for entity-based search queries.
    It converts to a QueryCondition that can be added to BatchQuerier conditions.
    """

    @abstractmethod
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition."""
        raise NotImplementedError


type QueryOrder = sa.sql.expression.UnaryExpression[Any] | sa.sql.expression.ColumnElement[Any]

# Factory function that creates a cursor condition from a decoded cursor value (str or UUID)
type CursorConditionFactory = Callable[[str], QueryCondition]

TRow = TypeVar("TRow", bound="Row[Any]")


@dataclass
class ScopeValidationArgs:
    user_id: UUID
    action_scope: ActionScope
    operation: OperationType
    entity_type: EntityType


@dataclass
class EntityValidationArgs:
    user_id: UUID
    action_scope: ActionScope
    operation: OperationType
    entity_id: ObjectId
