"""Pagination strategies for repository queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Optional

import sqlalchemy as sa

from .types import QueryCondition, QueryOrder, TRow

if TYPE_CHECKING:
    from sqlalchemy.engine import Row


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
    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info and slice rows if needed.

        Args:
            rows: The rows returned from query (may include extra row for page detection)
            total_count: Total count of items matching the query

        Returns:
            _PageInfoResult containing sliced rows and pagination flags
        """

        raise NotImplementedError


@dataclass
class PageInfoResult(Generic[TRow]):
    """Result of compute_page_info containing sliced rows and pagination flags."""

    rows: list[TRow]
    has_next_page: bool
    has_previous_page: bool


@dataclass
class OffsetPagination(QueryPagination):
    """
    Offset-based pagination using limit and offset.

    This is the traditional SQL pagination approach where you specify:
    - limit: Maximum number of items to return
    - offset: Number of items to skip from the beginning
    """

    limit: int
    """Maximum number of items to return (must be positive)."""

    offset: int = 0
    """Number of items to skip from the beginning (must be non-negative)."""

    @property
    def uses_window_function(self) -> bool:
        return True

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """Apply offset-based pagination to query."""

        query = query.limit(self.limit)
        if self.offset > 0:
            query = query.offset(self.offset)
        return query

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for offset-based pagination."""

        has_previous_page = self.offset > 0
        has_next_page = (self.offset + len(rows)) < total_count
        return PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )


@dataclass
class CursorForwardPagination(QueryPagination):
    """
    Cursor-based forward pagination using first and after.

    This follows the GraphQL Relay Cursor Connections specification for forward pagination.
    Use this to paginate forward through a result set:
    - first: Number of items to return from the cursor position
    - cursor_condition: Optional QueryCondition for WHERE clause (e.g., id > cursor_id).
      If None, starts from the beginning.
    - cursor_order: QueryOrder for cursor-based ordering (e.g., created_at ASC)
    """

    first: int
    """Number of items to return (must be positive)."""

    cursor_order: QueryOrder
    """Ordering for cursor-based pagination (e.g., ORDER BY created_at ASC)."""

    cursor_condition: Optional[QueryCondition] = None
    """Optional QueryCondition for cursor position. If None, starts from the beginning."""

    @property
    def uses_window_function(self) -> bool:
        return False

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based forward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_next_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.first + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for cursor-based forward pagination."""

        # has_previous_page is True only if cursor was provided (meaning we're past the first page)
        has_previous_page = self.cursor_condition is not None
        has_next_page = len(rows) > self.first
        if has_next_page:
            rows = rows[: self.first]
        return PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )


@dataclass
class CursorBackwardPagination(QueryPagination):
    """
    Cursor-based backward pagination using last and before.

    This follows the GraphQL Relay Cursor Connections specification for backward pagination.
    Use this to paginate backward through a result set:
    - last: Number of items to return before the cursor position
    - cursor_condition: Optional QueryCondition for WHERE clause (e.g., id < cursor_id).
      If None, starts from the end.
    - cursor_order: QueryOrder for cursor-based ordering (e.g., created_at DESC for reverse fetch)
    """

    last: int
    """Number of items to return (must be positive)."""

    cursor_order: QueryOrder
    """Ordering for cursor-based pagination (e.g., ORDER BY created_at DESC)."""

    cursor_condition: Optional[QueryCondition] = None
    """Optional QueryCondition for cursor position. If None, starts from the end."""

    @property
    def uses_window_function(self) -> bool:
        return False

    def apply(self, query: sa.sql.Select) -> sa.sql.Select:
        """
        Apply cursor-based backward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_previous_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.last + 1)

    def compute_page_info(self, rows: list[Row], total_count: int) -> PageInfoResult[Row]:
        """Compute pagination info for cursor-based backward pagination."""

        # has_next_page is True only if cursor was provided (meaning there are items after this page)
        has_next_page = self.cursor_condition is not None
        has_previous_page = len(rows) > self.last
        if has_previous_page:
            rows = rows[: self.last]
        return PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )
