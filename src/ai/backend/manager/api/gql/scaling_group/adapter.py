"""GraphQL adapters for converting scaling group filters to repository queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.api.gql.base import decode_cursor
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)

if TYPE_CHECKING:
    from .types import ScalingGroupFilterGQL, ScalingGroupOrderByGQL

__all__ = ("ScalingGroupGQLAdapter",)


class ScalingGroupGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL scaling group queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[ScalingGroupFilterGQL] = None,
        order_by: Optional[list[ScalingGroupOrderByGQL]] = None,
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

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            for order in order_by:
                orders.append(order.to_query_order())

        # Build cursor condition and default order for cursor-based pagination
        cursor_condition: Optional[QueryCondition] = None
        default_order: Optional[QueryOrder] = None

        if after:
            cursor_value = decode_cursor(after)
            cursor_condition = ScalingGroupConditions.by_name_greater_than(cursor_value)
            default_order = ScalingGroupOrders.name(ascending=True)
        elif before:
            cursor_value = decode_cursor(before)
            cursor_condition = ScalingGroupConditions.by_name_less_than(cursor_value)
            default_order = ScalingGroupOrders.name(ascending=False)

        pagination = self.build_pagination(
            first,
            after,
            last,
            before,
            limit,
            offset,
            cursor_condition=cursor_condition,
            default_order=default_order,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
