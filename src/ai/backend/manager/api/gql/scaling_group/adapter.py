"""GraphQL adapters for converting scaling group filters to repository queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
)

if TYPE_CHECKING:
    from .types import ScalingGroupFilter, ScalingGroupOrderBy

__all__ = ("ScalingGroupGQLAdapter",)


class ScalingGroupGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL scaling group queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[ScalingGroupFilter] = None,
        order_by: Optional[ScalingGroupOrderBy] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Querier:
        """Build Querier from GraphQL filter, order_by, and pagination."""
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            orders.append(order_by.to_query_order())

        pagination = self.build_pagination(first, after, last, before, limit, offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
