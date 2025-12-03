"""GraphQL adapters for converting notification filters to repository queries."""

from __future__ import annotations

from typing import Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)

from .types import (
    NotificationChannelFilter,
    NotificationChannelOrderBy,
    NotificationRuleFilter,
    NotificationRuleOrderBy,
)

__all__ = (
    "NotificationChannelGQLAdapter",
    "NotificationRuleGQLAdapter",
)


class NotificationChannelGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL notification channel queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[NotificationChannelFilter] = None,
        order_by: Optional[NotificationChannelOrderBy] = None,
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
            orders.append(order_by.to_query_order())

        # Default order is created_at DESC (newest first)
        default_order: QueryOrder = NotificationChannelOrders.created_at(ascending=False)

        pagination = self.build_pagination(
            first,
            after,
            last,
            before,
            limit,
            offset,
            forward_cursor_condition_factory=NotificationChannelConditions.by_cursor_forward,
            backward_cursor_condition_factory=NotificationChannelConditions.by_cursor_backward,
            default_order=default_order,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)


class NotificationRuleGQLAdapter(BaseGQLAdapter):
    """Adapter for converting GraphQL notification rule queries to repository Querier."""

    def build_querier(
        self,
        filter: Optional[NotificationRuleFilter] = None,
        order_by: Optional[NotificationRuleOrderBy] = None,
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
            orders.append(order_by.to_query_order())

        # Default order is created_at DESC (newest first)
        default_order: QueryOrder = NotificationRuleOrders.created_at(ascending=False)

        pagination = self.build_pagination(
            first,
            after,
            last,
            before,
            limit,
            offset,
            forward_cursor_condition_factory=NotificationRuleConditions.by_cursor_forward,
            backward_cursor_condition_factory=NotificationRuleConditions.by_cursor_backward,
            default_order=default_order,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
