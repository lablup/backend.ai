"""GraphQL adapters for converting scaling group filters to repository queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
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
        # Cursor pagination and order_by are mutually exclusive
        is_cursor_pagination = first is not None or last is not None
        if is_cursor_pagination and order_by is not None:
            raise InvalidGraphQLParameters(
                "order_by cannot be used with cursor pagination (first/after, last/before)"
            )

        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []

        if filter:
            conditions.extend(filter.build_conditions())

        # Apply client-specified order (only for offset pagination)
        if order_by:
            for order in order_by:
                orders.append(order.to_query_order())

        # Default order is created_at DESC (newest first) for cursor pagination
        default_order: QueryOrder = ScalingGroupOrders.created_at(ascending=False)

        pagination = self.build_pagination(
            first,
            after,
            last,
            before,
            limit,
            offset,
            forward_cursor_condition_factory=ScalingGroupConditions.by_cursor_forward,
            backward_cursor_condition_factory=ScalingGroupConditions.by_cursor_backward,
            default_order=default_order,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
