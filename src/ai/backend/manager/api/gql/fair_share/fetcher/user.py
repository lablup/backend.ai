"""User Fair Share fetcher functions."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    UserFairShareConnection,
    UserFairShareEdge,
    UserFairShareFilter,
    UserFairShareGQL,
    UserFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.fair_share.options import (
    UserFairShareConditions,
    UserFairShareOrders,
)
from ai.backend.manager.services.fair_share.actions import SearchUserFairSharesAction


@lru_cache(maxsize=1)
def get_user_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=UserFairShareOrders.by_created_at(ascending=False),
        backward_order=UserFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=UserFairShareConditions.by_cursor_forward,
        backward_condition_factory=UserFairShareConditions.by_cursor_backward,
    )


async def fetch_user_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: UserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> UserFairShareConnection:
    """Fetch user fair shares with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., project_id filter)
    """
    processors = info.context.processors

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_user_fair_share_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processors.fair_share.search_user_fair_shares.wait_for_complete(
        SearchUserFairSharesAction(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
    )

    nodes = [UserFairShareGQL.from_dataclass(data) for data in action_result.items]
    edges = [UserFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
