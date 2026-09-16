"""Pagination utilities shared by GQL and REST adapters.

Provides PaginationOptions, PaginationSpec, and build_pagination() used by
both the GQL adapter (BaseGQLAdapter) and domain adapters (BaseAdapter).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.sql import operators
from sqlalchemy.sql.expression import UnaryExpression

from ai.backend.manager.api.adapter_options.cursor.cursor import decode_cursor
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    QueryPagination,
)
from ai.backend.manager.repositories.base import CursorConditionFactory

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


def _order_column(order: QueryOrder) -> sa.ColumnElement[Any]:
    if isinstance(order, UnaryExpression):
        return order.element
    return order


def _is_descending(order: QueryOrder) -> bool:
    return isinstance(order, UnaryExpression) and order.modifier is operators.desc_op


def _reverse_order(order: QueryOrder) -> QueryOrder:
    column = _order_column(order)
    return column.asc() if _is_descending(order) else column.desc()


def _parse_cursor_id(id_column: sa.ColumnElement[Any], cursor_id: str) -> Any:
    if isinstance(id_column.type, GUID):
        try:
            return uuid.UUID(cursor_id)
        except ValueError as e:
            raise InvalidCursor(f"Invalid cursor value: {cursor_id}") from e
    return cursor_id


@dataclass(frozen=True)
class PaginationSpec:
    """Cursor pagination contract of one entity.

    ``forward_order`` is the page order of ``first``/``after``; ``last``/``before`` walks
    its reverse. ``tiebreaker_order`` comes last in both directions (reversed for backward)
    and its column is the row identity a cursor encodes, so it must be unique.
    """

    forward_order: QueryOrder
    tiebreaker_order: QueryOrder
    backward_order: QueryOrder | None = None
    forward_condition_factory: CursorConditionFactory | None = None
    backward_condition_factory: CursorConditionFactory | None = None

    @property
    def backward_tiebreaker_order(self) -> QueryOrder:
        return _reverse_order(self.tiebreaker_order)

    def cursor_order(self, *, backward: bool = False) -> QueryOrder:
        if not backward:
            return self.forward_order
        if self.backward_order is not None:
            return self.backward_order
        return _reverse_order(self.forward_order)

    def build_cursor_condition(self, cursor_id: str, *, backward: bool = False) -> QueryCondition:
        """Rows past the cursor row in ``(forward_order, tiebreaker_order)``; before it when
        ``backward``. ``cursor_id`` is the decoded cursor, the value of the tiebreaker column."""
        factory = self.backward_condition_factory if backward else self.forward_condition_factory
        if factory is not None:
            try:
                return factory(cursor_id)
            except ValueError as e:
                raise InvalidCursor(f"Invalid cursor value: {cursor_id}") from e
        sort_column = _order_column(self.forward_order)
        id_column = _order_column(self.tiebreaker_order)
        cursor_value = _parse_cursor_id(id_column, cursor_id)
        sort_less = _is_descending(self.forward_order) != backward
        id_less = _is_descending(self.tiebreaker_order) != backward

        def inner() -> sa.ColumnElement[bool]:
            sort_at_cursor = (
                sa.select(sort_column).where(id_column == cursor_value).scalar_subquery()
            )
            return sa.or_(
                sort_column < sort_at_cursor if sort_less else sort_column > sort_at_cursor,
                sa.and_(
                    sort_column == sort_at_cursor,
                    id_column < cursor_value if id_less else id_column > cursor_value,
                ),
            )

        return inner


def build_pagination(
    options: PaginationOptions,
    spec: PaginationSpec,
) -> QueryPagination:
    """Build QueryPagination from pagination arguments and domain spec.

    For cursor-based pagination (first/after or last/before), the cursor condition
    and order come from the spec. For offset pagination, returns OffsetPagination.
    If no parameters are provided, returns a default OffsetPagination.

    Args:
        options: Flat pagination arguments (first/after/last/before/limit/offset).
        spec: Domain-specific pagination specification (orders).

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
            cursor_condition = spec.build_cursor_condition(decode_cursor(options.after))
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
            cursor_condition = spec.build_cursor_condition(
                decode_cursor(options.before), backward=True
            )
        return CursorBackwardPagination(
            last=options.last,
            cursor_order=spec.cursor_order(backward=True),
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
