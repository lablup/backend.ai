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
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorConditionFactory,
    CursorForwardPagination,
    OffsetPagination,
    QueryCondition,
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

    @property
    def has_forward_cursor(self) -> bool:
        return self.first is not None or self.after is not None

    @property
    def has_backward_cursor(self) -> bool:
        return self.last is not None or self.before is not None

    @property
    def has_cursor(self) -> bool:
        return self.has_forward_cursor or self.has_backward_cursor

    @property
    def has_offset(self) -> bool:
        return self.limit is not None or self.offset is not None


@dataclass(frozen=True)
class PaginationSpec:
    """Domain-specific configuration for cursor-based pagination.

    With ``cursor_column`` given, ``cursor_column`` ASC breaks ties of
    ``forward_order``, backward pagination reverses both, and the cursor
    conditions are derived from the two.

    Entities whose table has no unique UUID column cannot carry a row UUID in
    the cursor. They give ``explicit_backward_order``,
    ``explicit_tiebreaker_order`` and the two condition factories instead, and
    keep their per-entity cursor conditions.
    """

    forward_order: QueryOrder
    """Order for forward pagination (e.g., created_at DESC for newest first).
    Also used as default order for offset pagination when order is not provided."""

    cursor_column: QueryableAttribute[Any] | None = None
    """Unique UUID column whose value the cursor carries."""

    explicit_backward_order: QueryOrder | None = None
    """Order for backward pagination, when it is not derived from the cursor column."""

    explicit_tiebreaker_order: QueryOrder | None = None
    """Tiebreaker order, when it is not derived from the cursor column."""

    forward_condition_factory: CursorConditionFactory | None = None
    """Per-entity forward cursor condition, when it is not derived from the cursor column."""

    backward_condition_factory: CursorConditionFactory | None = None
    """Per-entity backward cursor condition, when it is not derived from the cursor column."""

    @property
    def backward_order(self) -> QueryOrder:
        if self.cursor_column is None:
            return self._required(self.explicit_backward_order, "explicit_backward_order")
        column, ascending = self._unpack(self.forward_order)
        if ascending:
            return column.desc()
        return column.asc()

    @property
    def tiebreaker_order(self) -> QueryOrder:
        """Last ORDER BY clause of forward and offset pagination."""
        if self.cursor_column is None:
            return self._required(self.explicit_tiebreaker_order, "explicit_tiebreaker_order")
        ascending: QueryOrder = self.cursor_column.asc()
        return ascending

    @property
    def backward_tiebreaker_order(self) -> QueryOrder:
        """Last ORDER BY clause of backward pagination."""
        if self.cursor_column is None:
            return self._required(self.explicit_tiebreaker_order, "explicit_tiebreaker_order")
        descending: QueryOrder = self.cursor_column.desc()
        return descending

    def forward_condition(self, cursor: str) -> QueryCondition:
        """Condition selecting the rows after the cursor row in forward order."""
        if self.cursor_column is None:
            factory = self._required(self.forward_condition_factory, "forward_condition_factory")
            return factory(cursor)
        return self._condition(self.forward_order, True, cursor)

    def backward_condition(self, cursor: str) -> QueryCondition:
        """Condition selecting the rows after the cursor row in backward order."""
        if self.cursor_column is None:
            factory = self._required(self.backward_condition_factory, "backward_condition_factory")
            return factory(cursor)
        return self._condition(self.backward_order, False, cursor)

    def _required[T](self, value: T | None, name: str) -> T:
        if value is None:
            raise ServerMisconfiguredError(
                f"Pagination spec without a cursor column must set {name}"
            )
        return value

    def _condition(
        self, order: QueryOrder, tiebreaker_ascending: bool, cursor: str
    ) -> QueryCondition:
        cursor_value = UUID(cursor)
        cursor_attribute = self._required(self.cursor_column, "cursor_column")

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            cursor_column = cursor_attribute.expression
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
    if sum([options.has_forward_cursor, options.has_backward_cursor, options.has_offset]) > 1:
        raise InvalidGraphQLParameters(
            "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
        )

    if options.first is not None:
        if options.first <= 0:
            raise InvalidGraphQLParameters(f"first must be positive, got {options.first}")
        cursor_condition = None
        if options.after is not None:
            cursor_value = decode_cursor(options.after)
            try:
                cursor_condition = spec.forward_condition(cursor_value)
            except ValueError as e:
                raise InvalidCursor(f"Invalid cursor value: {options.after}") from e
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
            try:
                cursor_condition = spec.backward_condition(cursor_value)
            except ValueError as e:
                raise InvalidCursor(f"Invalid cursor value: {options.before}") from e
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
