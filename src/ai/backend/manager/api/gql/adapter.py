"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from typing import Any

from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions as PaginationOptions,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationSpec as PaginationSpec,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import build_pagination
from ai.backend.manager.repositories.base import BatchQuerier, QueryOrder


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
        a QueryOrder. For offset/default pagination, if no order_by is given,
        spec.forward_order is used as the default. The tiebreaker order is
        always appended last, reversed for backward pagination.
        """
        pagination = build_pagination(options, spec)
        is_cursor_pagination = options.first is not None or options.last is not None

        orders: list[QueryOrder] = []
        if order_by:
            orders.extend(item.to_query_order() for item in order_by)
        elif not is_cursor_pagination:
            orders.append(spec.forward_order)
        if options.last is not None:
            orders.append(spec.backward_tiebreaker_order)
        else:
            orders.append(spec.tiebreaker_order)

        return BatchQuerier(conditions=[], orders=orders, pagination=pagination)
