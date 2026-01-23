from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict

# QueryCondition now returns a ColumnElement (whereclause) instead of modifying stmt
type QueryCondition = Callable[[], sa.sql.expression.ColumnElement[bool]]

type QueryOrder = sa.sql.expression.UnaryExpression | sa.sql.expression.ColumnElement

TRow = TypeVar("TRow")


class QueryPagination(ABC):
    """
    Base class for pagination strategies.

    Subclasses must implement the apply() method to transform a SQLAlchemy
    select statement with appropriate pagination logic.
    """

    @property
    @abstractmethod
    def uses_window_function(self) -> bool:
        """Whether this pagination uses window function for total_count.

        Returns:
            True if window function should be added to main query (Offset),
            False if separate count query should be used (Cursor).
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply pagination to a SQLAlchemy select statement."""

        raise NotImplementedError

    @abstractmethod
    def compute_page_info(self, rows: list, total_count: int) -> PageInfoResult:
        """Compute pagination info and slice rows if needed.

        Args:
            rows: The rows returned from query (may include extra row for page detection)
            total_count: Total count of items matching the query

        Returns:
            _PageInfoResult containing sliced rows and pagination flags
        """

        raise NotImplementedError


@dataclass
class PageInfoResult:
    """Result of compute_page_info containing sliced rows and pagination flags."""

    has_next_page: bool
    has_previous_page: bool


class CreateSpec(BaseModel):
    model_config = ConfigDict(
        strict=True,
        arbitrary_types_allowed=True,
    )


@dataclass
class Querier:
    pk_value: UUID | str | int


@dataclass
class BatchQuerier:
    """Bundles query conditions, orders, and pagination for batch repository queries."""

    pagination: QueryPagination
    conditions: list[QueryCondition] = field(default_factory=list)
    orders: list[QueryOrder] = field(default_factory=list)


@dataclass
class BatchQuerierResult(Generic[TRow]):
    """Result of executing a batch query with querier."""

    rows: list[TRow]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


class UpdateSpec(BaseModel):
    model_config = ConfigDict(
        strict=True,
        arbitrary_types_allowed=True,
    )

    pk_value: UUID | str | int
