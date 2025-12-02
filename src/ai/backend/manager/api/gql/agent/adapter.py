from typing import TYPE_CHECKING, Optional

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
from ai.backend.manager.repositories.base import (
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.agent.types import AgentFilterGQL, AgentOrderByGQL


__all__ = ("AgentGQLAdapter",)


class AgentGQLAdapter(BaseGQLAdapter):
    """
    Adapter for converting GraphQL Agent queries to repository Querier.
    """

    def build_querier(
        self,
        filter: Optional["AgentFilterGQL"] = None,
        order_by: Optional[list["AgentOrderByGQL"]] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Querier:
        conditions: list[QueryCondition] = []
        orders: list[QueryOrder] = []
        pagination: Optional[QueryPagination] = None

        if filter:
            conditions.extend(filter.build_conditions())
        if order_by:
            for order in order_by:
                orders.append(order.to_query_order())

        pagination = self.build_pagination(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )

        return Querier(conditions=conditions, orders=orders, pagination=pagination)
