"""GraphQL adapters for converting notification filters to repository queries."""

from __future__ import annotations

from typing import Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
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
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            orders.append(order_by.to_query_order())

        pagination = self.build_pagination(first, after, last, before, limit, offset)

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
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())

        if order_by:
            orders.append(order_by.to_query_order())

        pagination = self.build_pagination(first, after, last, before, limit, offset)

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
