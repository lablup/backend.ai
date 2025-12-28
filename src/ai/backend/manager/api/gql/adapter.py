"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, final

from ai.backend.manager.api.gql.base import decode_cursor
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    BatchQuerier,
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
    """GraphQL pagination arguments."""

    first: Optional[int] = None
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass(frozen=True)
class PaginationSpec:
    """Specification for pagination behavior.

    Contains domain-specific configuration for pagination:
    - Forward/backward orders and condition factories for cursor-based pagination
    - forward_order is also used as default order for offset pagination when order_by is not provided

    For typical "newest first" lists:
    - Forward (first/after): DESC order, shows newer items first, next page shows older items
    - Backward (last/before): ASC order, fetches older items first (reversed for display)
    """

    forward_order: QueryOrder
    """Order for forward pagination (e.g., created_at DESC for newest first).
    Also used as default order for offset pagination when order_by is not provided."""

    backward_order: QueryOrder
    """Order for backward pagination (e.g., created_at ASC, results reversed for display)."""

    forward_condition_factory: CursorConditionFactory
    """Factory that creates cursor condition for forward pagination (e.g., created_at < cursor)."""

    backward_condition_factory: CursorConditionFactory
    """Factory that creates cursor condition for backward pagination (e.g., created_at > cursor)."""


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""

    def _build_pagination(
        self,
        options: PaginationOptions,
        spec: PaginationSpec,
    ) -> QueryPagination:
        """Build pagination from GraphQL pagination arguments.

        For cursor-based pagination (first/after or last/before), condition factories
        and orders are used from the spec. The factories create cursor conditions from
        decoded cursor values.

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
                cursor_condition = spec.forward_condition_factory(cursor_value)
            return CursorForwardPagination(
                first=options.first,
                cursor_order=spec.forward_order,
                cursor_condition=cursor_condition,
            )
        elif options.last is not None:
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
        pagination_spec: PaginationSpec,
        filter: Optional[GQLFilter] = None,
        order_by: Optional[Sequence[GQLOrderBy]] = None,
        base_conditions: Optional[Sequence[QueryCondition]] = None,
    ) -> BatchQuerier:
        """Build BatchQuerier from GraphQL arguments with domain configuration.

        Args:
            pagination_options: Pagination parameters (first/after/last/before/limit/offset)
            pagination_spec: Domain-specific pagination specification (orders, condition factories)
            filter: Optional filter with build_conditions() method
            order_by: Optional sequence of order specifications with to_query_order() method
            base_conditions: Optional base conditions to prepend (e.g., deployment_id filter)

        Returns:
            A BatchQuerier instance with conditions, orders, and pagination configured.

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

        # Prepend base conditions first (e.g., deployment_id filter)
        if base_conditions:
            conditions.extend(base_conditions)

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            for o in order_by:
                orders.append(o.to_query_order())
        elif not is_cursor_pagination:
            # Apply default order for offset pagination when order_by is not provided
            orders.append(pagination_spec.forward_order)

        pagination = self._build_pagination(
            options=pagination_options,
            spec=pagination_spec,
        )

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)
