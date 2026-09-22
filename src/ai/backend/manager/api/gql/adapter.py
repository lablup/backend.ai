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
<<<<<<< HEAD
        a QueryOrder. For offset/default pagination, if no order_by is given,
        spec.forward_order is used as the default. spec.tiebreaker_order is
        always appended last.
        """
        pagination = build_pagination(options, spec)
        is_cursor_pagination = options.first is not None or options.last is not None

        orders: list[QueryOrder] = []
        if order_by:
            orders.extend(item.to_query_order() for item in order_by)
        elif not is_cursor_pagination:
            orders.append(spec.forward_order)
        orders.append(spec.tiebreaker_order)

        return BatchQuerier(conditions=[], orders=orders, pagination=pagination)
=======
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
>>>>>>> 82b68f24 (fix(BA-8084): drop the caller's order under cursor pagination (#14922))
