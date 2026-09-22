"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from typing import Any

from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions as PaginationOptions,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationSpec as PaginationSpec,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    build_orders,
    build_pagination,
)
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.repositories.base import BatchQuerier


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""

    @staticmethod
    def build_querier(
        options: PaginationOptions,
        spec: PaginationSpec,
        *,
        order_by: list[Any] | None = None,
    ) -> BatchQuerier:
        """Build a BatchQuerier from pagination options and domain spec.

        Each item in order_by must have a to_query_order() method that returns
        a QueryOrder. Cursor pagination drops order_by; offset pagination applies
        it, or spec.forward_order if absent. The tiebreaker order is always
        appended last, reversed for backward pagination.
        """
        pagination = build_pagination(options, spec)
        orders: list[QueryOrder] = [item.to_query_order() for item in order_by or ()]
        final_orders = build_orders(options, spec, orders)
        return BatchQuerier(
            conditions=[],
            orders=final_orders,
            pagination=pagination,
        )
