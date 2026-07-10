"""Pagination strategies for repository queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

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

    @abstractmethod
    def apply(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """Apply pagination to a SQLAlchemy select statement."""

        raise NotImplementedError

    @abstractmethod
    def compute_page_info(self, rows: list[Row[Any]], total_count: int) -> PageInfoResult[Row[Any]]:
        """Compute pagination info and slice rows if needed.

        Args:
            rows: The rows returned from query (may include extra row for page detection)
            total_count: Total count of items matching the query

        Returns:
            _PageInfoResult containing sliced rows and pagination flags
        """

        raise NotImplementedError

    @abstractmethod
    def attach_count(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """Attach a total_count column to the data query if this strategy folds
        counting into the data query; otherwise return the query unchanged.
        """

        raise NotImplementedError

    @abstractmethod
    def count_from_rows(self, rows: list[Row[Any]]) -> int | None:
        """Derive total_count from the fetched rows.

        Returns:
            The total count if derivable from the rows, or None to signal the
            caller must execute a separate count query.
        """

        raise NotImplementedError


@dataclass
class PageInfoResult[TRow]:
    """Result of compute_page_info containing sliced rows and pagination flags."""

    rows: list[TRow]
    has_next_page: bool
    has_previous_page: bool


@dataclass
class NoPagination(QueryPagination):
    """
    No pagination - returns all matching rows.

    Use this when you need to fetch all results without any limit.
    Useful for internal operations like scheduler batch processing.
    """

    @override
    def apply(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """No pagination applied - returns query unchanged."""
        return query

    def compute_page_info(
        self, rows: list[Row[Any]], _total_count: int
    ) -> PageInfoResult[Row[Any]]:
        """No pagination - no next/previous pages."""
        return PageInfoResult(
            rows=rows,
            has_next_page=False,
            has_previous_page=False,
        )

    @override
    def attach_count(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """No count column needed - all rows are returned."""
        return query

    @override
    def count_from_rows(self, rows: list[Row[Any]]) -> int | None:
        """All matching rows are returned, so the count is simply len(rows)."""
        return len(rows)


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

    @override
    def apply(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """Apply offset-based pagination to query."""

        query = query.limit(self.limit)
        if self.offset > 0:
            query = query.offset(self.offset)
        return query

    def compute_page_info(self, rows: list[Row[Any]], total_count: int) -> PageInfoResult[Row[Any]]:
        """Compute pagination info for offset-based pagination."""

        has_previous_page = self.offset > 0
        has_next_page = (self.offset + len(rows)) < total_count
        return PageInfoResult(
            rows=rows,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    @override
    def attach_count(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """Fold the total count into the data query via a window function."""
        return query.add_columns(sa.func.count().over().label("total_count"))

    @override
    def count_from_rows(self, rows: list[Row[Any]]) -> int | None:
        """Read the window-function count from the rows.

        Returns None when there are no rows (the window column is absent), so the
        caller falls back to a separate count query.
        """
        if rows:
            total_count: int = rows[0].total_count
            return total_count
        return None


class CursorPagination(QueryPagination):
    """Shared count strategy for cursor-based pagination.

    total_count comes from a separate count query: a window count would be wrong
    because the data query fetches LIMIT N+1 rows for page detection.
    """

    @override
    def attach_count(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        return query

    @override
    def count_from_rows(self, rows: list[Row[Any]]) -> int | None:
        return None


@dataclass
class CursorForwardPagination(CursorPagination):
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

    cursor_condition: QueryCondition | None = None
    """Optional QueryCondition for cursor position. If None, starts from the beginning."""

    @override
    def apply(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """
        Apply cursor-based forward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_next_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.first + 1)

    def compute_page_info(
        self, rows: list[Row[Any]], _total_count: int
    ) -> PageInfoResult[Row[Any]]:
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
class CursorBackwardPagination(CursorPagination):
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

    cursor_condition: QueryCondition | None = None
    """Optional QueryCondition for cursor position. If None, starts from the end."""

    @override
    def apply(self, query: sa.sql.Select[Any]) -> sa.sql.Select[Any]:
        """
        Apply cursor-based backward pagination to query.

        Applies cursor condition (if present), cursor order, and LIMIT + 1 for has_previous_page detection.
        """
        if self.cursor_condition is not None:
            query = query.where(self.cursor_condition())
        query = query.order_by(self.cursor_order)
        return query.limit(self.last + 1)

    def compute_page_info(
        self, rows: list[Row[Any]], _total_count: int
    ) -> PageInfoResult[Row[Any]]:
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
