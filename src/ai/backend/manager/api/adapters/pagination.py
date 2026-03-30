"""Pagination utilities shared by GQL and REST adapters.

Provides PaginationOptions, PaginationSpec, and build_pagination() used by
both the GQL adapter (BaseGQLAdapter) and domain adapters (BaseAdapter).
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorConditionFactory,
    CursorForwardPagination,
    OffsetPagination,
    QueryOrder,
    QueryPagination,
)

from .cursor import decode_cursor

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

    For typical "newest first" lists:
    - Forward (first/after): DESC order, shows newer items first
    - Backward (last/before): ASC order, fetches older items first (reversed for display)
    """

    forward_order: QueryOrder
    """Order for forward pagination (e.g., created_at DESC for newest first).
    Also used as default order for offset pagination when order is not provided."""

    backward_order: QueryOrder
    """Order for backward pagination (e.g., created_at ASC, results reversed for display)."""

    forward_condition_factory: CursorConditionFactory
    """Factory that creates cursor condition for forward pagination (e.g., created_at < cursor)."""

    backward_condition_factory: CursorConditionFactory
    """Factory that creates cursor condition for backward pagination (e.g., created_at > cursor)."""

    tiebreaker_order: QueryOrder
    """Tiebreaker order for deterministic pagination (e.g., RowClass.id.asc()).
    Applied as the last ORDER BY clause to ensure stable ordering."""


def build_pagination(
    options: PaginationOptions,
    spec: PaginationSpec,
) -> QueryPagination:
    """Build QueryPagination from pagination arguments and domain spec.

    For cursor-based pagination (first/after or last/before), condition factories
    and orders are taken from the spec. For offset pagination, returns OffsetPagination.
    If no parameters are provided, returns a default OffsetPagination.

    Args:
        options: Flat pagination arguments (first/after/last/before/limit/offset).
        spec: Domain-specific pagination specification (orders, condition factories).

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
            cursor_condition = spec.forward_condition_factory(cursor_value)
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
            cursor_condition = spec.backward_condition_factory(cursor_value)
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
