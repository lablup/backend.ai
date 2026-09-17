"""Pagination utilities shared by GQL and REST adapters.

Provides PaginationOptions, PaginationSpec, and build_pagination() used by
both the GQL adapter (BaseGQLAdapter) and domain adapters (BaseAdapter).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import QueryableAttribute
from sqlalchemy.sql import operators

from ai.backend.manager.api.adapter_options.cursor.cursor import decode_cursor
<<<<<<< HEAD
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
=======
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import (
>>>>>>> e643d3184 (fix(BA-7979): include the tiebreaker in cursor pagination conditions (#14734))
    CursorBackwardPagination,
    CursorConditionFactory,
    CursorForwardPagination,
    OffsetPagination,
    QueryOrder,
    QueryPagination,
)

DEFAULT_PAGINATION_LIMIT = 10


@dataclass(frozen=True)
class PaginationOptions:
    """Pagination arguments (flat form, used by GQL and adapter search inputs)."""

    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class PaginationSpec:
    """Domain-specific configuration for cursor-based pagination.

    ``cursor_column`` ASC breaks ties of ``forward_order``.
    Backward pagination reverses both.
    """

    forward_order: QueryOrder
    """Order for forward pagination (e.g., created_at DESC for newest first).
    Also used as default order for offset pagination when order is not provided."""

    cursor_column: QueryableAttribute[Any]
    """Unique UUID column whose value the cursor carries."""

    @property
    def backward_order(self) -> QueryOrder:
        column, ascending = self._unpack(self.forward_order)
        if ascending:
            return column.desc()
        return column.asc()

    @property
    def tiebreaker_order(self) -> QueryOrder:
        """Last ORDER BY clause of forward and offset pagination."""
        return self.cursor_column.asc()

    @property
    def backward_tiebreaker_order(self) -> QueryOrder:
        """Last ORDER BY clause of backward pagination."""
        return self.cursor_column.desc()

    def forward_condition(self, cursor: str) -> QueryCondition:
        """Condition selecting the rows after the cursor row in forward order."""
        return self._condition(self.forward_order, True, cursor)

    def backward_condition(self, cursor: str) -> QueryCondition:
        """Condition selecting the rows after the cursor row in backward order."""
        return self._condition(self.backward_order, False, cursor)

    def _condition(
        self, order: QueryOrder, tiebreaker_ascending: bool, cursor: str
    ) -> QueryCondition:
        cursor_value = UUID(cursor)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_column = self.cursor_column.expression
            order_column, order_ascending = self._unpack(order)
            if order_column.compare(cursor_column):
                return self._past(cursor_column, order_ascending, cursor_value)
            cursor_row_value = (
                sa.select(order_column).where(cursor_column == cursor_value).scalar_subquery()
            )
            return sa.or_(
                self._past(order_column, order_ascending, cursor_row_value),
                sa.and_(
                    order_column == cursor_row_value,
                    self._past(cursor_column, tiebreaker_ascending, cursor_value),
                ),
            )

        return inner

    def _past(
        self, column: sa.sql.expression.ColumnElement[Any], ascending: bool, value: Any
    ) -> sa.sql.expression.ColumnElement[bool]:
        past: sa.sql.expression.ColumnElement[bool] = (
            column > value if ascending else column < value
        )
        return past

    def _unpack(self, order: QueryOrder) -> tuple[sa.sql.expression.ColumnElement[Any], bool]:
        if isinstance(order, sa.sql.expression.UnaryExpression):
            if order.modifier is operators.asc_op:
                return order.element, True
            if order.modifier is operators.desc_op:
                return order.element, False
        raise ServerMisconfiguredError(f"Pagination order must be a plain ASC/DESC column: {order}")


def build_pagination(
    options: PaginationOptions,
    spec: PaginationSpec,
) -> QueryPagination:
    """Build QueryPagination from pagination arguments and domain spec.

    For cursor-based pagination (first/after or last/before), conditions
    and orders are taken from the spec. For offset pagination, returns OffsetPagination.
    If no parameters are provided, returns a default OffsetPagination.

    Args:
        options: Flat pagination arguments (first/after/last/before/limit/offset).
        spec: Domain-specific pagination specification (orders, cursor column).

    Raises:
        InvalidGraphQLParameters: If multiple pagination modes are requested
            or if first/last values are not positive.
    """
    has_forward_cursor = options.first is not None or options.after is not None
    has_backward_cursor = options.last is not None or options.before is not None
    has_offset = options.limit is not None or options.offset is not None

    if sum([has_forward_cursor, has_backward_cursor, has_offset]) > 1:
        raise InvalidGraphQLParameters(
            "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
        )

    if options.first is not None:
        if options.first <= 0:
            raise InvalidGraphQLParameters(f"first must be positive, got {options.first}")
        cursor_condition = None
        if options.after is not None:
            cursor_value = decode_cursor(options.after)
<<<<<<< HEAD
            cursor_condition = spec.forward_condition_factory(cursor_value)
=======
            try:
                cursor_condition = spec.forward_condition(cursor_value)
            except ValueError as e:
                raise InvalidCursor(f"Invalid cursor value: {options.after}") from e
>>>>>>> e643d3184 (fix(BA-7979): include the tiebreaker in cursor pagination conditions (#14734))
        return CursorForwardPagination(
            first=options.first,
            cursor_order=spec.forward_order,
            cursor_condition=cursor_condition,
        )

    if options.last is not None:
        if options.last <= 0:
            raise InvalidGraphQLParameters(f"last must be positive, got {options.last}")
        cursor_condition = None
        if options.before is not None:
            cursor_value = decode_cursor(options.before)
<<<<<<< HEAD
            cursor_condition = spec.backward_condition_factory(cursor_value)
=======
            try:
                cursor_condition = spec.backward_condition(cursor_value)
            except ValueError as e:
                raise InvalidCursor(f"Invalid cursor value: {options.before}") from e
>>>>>>> e643d3184 (fix(BA-7979): include the tiebreaker in cursor pagination conditions (#14734))
        return CursorBackwardPagination(
            last=options.last,
            cursor_order=spec.backward_order,
            cursor_condition=cursor_condition,
        )

    if options.limit is not None:
        if options.limit <= 0:
            raise InvalidGraphQLParameters(f"limit must be positive, got {options.limit}")
        if options.offset is not None and options.offset < 0:
            raise InvalidGraphQLParameters(f"offset must be non-negative, got {options.offset}")
        return OffsetPagination(limit=options.limit, offset=options.offset or 0)

    if options.offset is not None:
        if options.offset < 0:
            raise InvalidGraphQLParameters(f"offset must be non-negative, got {options.offset}")
        return OffsetPagination(limit=DEFAULT_PAGINATION_LIMIT, offset=options.offset)

    return OffsetPagination(limit=DEFAULT_PAGINATION_LIMIT, offset=0)
