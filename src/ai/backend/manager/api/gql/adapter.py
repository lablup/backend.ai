"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, final

from ai.backend.manager.api.gql.base import decode_cursor
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorConditionFactory,
    CursorForwardPagination,
    OffsetPagination,
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
)

DEFAULT_PAGINATION_LIMIT = 10


@dataclass(frozen=True)
class PaginationOptions:
    """GraphQL pagination arguments."""

    first: Optional[int] = None
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass(frozen=True)
class CursorPaginationFactories:
    """Factories for cursor-based pagination.

    Contains domain-specific factories needed for cursor-based pagination.
    """

    default_order: QueryOrder
    forward_cursor_condition_factory: CursorConditionFactory
    backward_cursor_condition_factory: CursorConditionFactory


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""

    def _build_pagination(
        self,
        options: PaginationOptions,
        factories: CursorPaginationFactories,
    ) -> QueryPagination:
        """Build pagination from GraphQL pagination arguments.

        For cursor-based pagination (first/after or last/before), cursor condition factories
        and default_order are required. The factories create cursor conditions from decoded
        cursor values.

        If no pagination parameters are provided, returns a default OffsetPagination
        with limit=DEFAULT_PAGINATION_LIMIT.
        """
        # Validate and build pagination
        # Count how many pagination modes are being used
        pagination_modes = sum([
            options.first is not None,
            options.last is not None,
            options.limit is not None,
        ])

        if pagination_modes > 1:
            raise InvalidGraphQLParameters(
                "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
            )

        # Build appropriate pagination based on parameters
        if options.first is not None:
            if options.first <= 0:
                raise InvalidGraphQLParameters(f"first must be positive, got {options.first}")
            cursor_condition = None
            if options.after is not None:
                cursor_value = decode_cursor(options.after)
                cursor_condition = factories.forward_cursor_condition_factory(cursor_value)
            return CursorForwardPagination(
                first=options.first,
                default_order=factories.default_order,
                cursor_condition=cursor_condition,
            )
        elif options.last is not None:
            if options.last <= 0:
                raise InvalidGraphQLParameters(f"last must be positive, got {options.last}")
            cursor_condition = None
            if options.before is not None:
                cursor_value = decode_cursor(options.before)
                cursor_condition = factories.backward_cursor_condition_factory(cursor_value)
            return CursorBackwardPagination(
                last=options.last,
                default_order=factories.default_order,
                cursor_condition=cursor_condition,
            )
        elif options.limit is not None:
            if options.limit <= 0:
                raise InvalidGraphQLParameters(f"limit must be positive, got {options.limit}")
            if options.offset is not None and options.offset < 0:
                raise InvalidGraphQLParameters(f"offset must be non-negative, got {options.offset}")
            return OffsetPagination(limit=options.limit, offset=options.offset or 0)

        # Default pagination when no parameters provided
        return OffsetPagination(limit=DEFAULT_PAGINATION_LIMIT, offset=0)

    @final
    def build_querier(
        self,
        pagination_options: PaginationOptions,
        cursor_pagination_factories: CursorPaginationFactories,
        filter: Optional[GQLFilter] = None,
        order_by: Optional[Sequence[GQLOrderBy]] = None,
    ) -> Querier:
        """Build Querier from GraphQL arguments with domain configuration.

        Args:
            pagination_options: Pagination parameters (first/after/last/before/limit/offset)
            cursor_pagination_factories: Domain-specific factories (cursor factories, default order)
            filter: Optional filter with build_conditions() method
            order_by: Optional sequence of order specifications with to_query_order() method

        Returns:
            A Querier instance with conditions, orders, and pagination configured.

        Raises:
            InvalidGraphQLParameters: If order_by is used with cursor pagination.
        """
        # Cursor pagination and order_by are mutually exclusive
        is_cursor_pagination = (
            pagination_options.first is not None or pagination_options.last is not None
        )
        if is_cursor_pagination and order_by is not None:
            raise InvalidGraphQLParameters(
                "order_by cannot be used with cursor pagination (first/after, last/before)"
            )

        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            for o in order_by:
                orders.append(o.to_query_order())

        pagination = self._build_pagination(
            options=pagination_options,
            factories=cursor_pagination_factories,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
