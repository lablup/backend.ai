"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import final

from ai.backend.manager.api.adapters.pagination import (
    PaginationOptions as PaginationOptions,
)
from ai.backend.manager.api.adapters.pagination import (
    PaginationSpec as PaginationSpec,
)
from ai.backend.manager.api.adapters.pagination import (
    build_pagination,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    QueryCondition,
    QueryOrder,
)


@dataclass(frozen=True)
class QuerierInput:
    """Internal input for build_querier_from_input. Contains adapter-level types only."""

    pagination: PaginationOptions = field(default_factory=PaginationOptions)
    filter: GQLFilter | None = None
    order_by: Sequence[GQLOrderBy] | None = None
    base_conditions: Sequence[QueryCondition] | None = None


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""

    @final
    def build_querier(
        self,
        pagination_options: PaginationOptions,
        pagination_spec: PaginationSpec,
        filter: GQLFilter | None = None,
        order_by: Sequence[GQLOrderBy] | None = None,
        base_conditions: Sequence[QueryCondition] | None = None,
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

        # Always append tiebreaker as the last ORDER BY for deterministic ordering
        orders.append(pagination_spec.tiebreaker_order)

        pagination = build_pagination(options=pagination_options, spec=pagination_spec)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    @final
    def build_querier_from_input(
        self,
        input: QuerierInput,
        pagination_spec: PaginationSpec,
    ) -> BatchQuerier:
        """Build BatchQuerier from a QuerierInput dataclass."""
        return self.build_querier(
            input.pagination,
            pagination_spec,
            filter=input.filter,
            order_by=input.order_by,
            base_conditions=input.base_conditions,
        )
