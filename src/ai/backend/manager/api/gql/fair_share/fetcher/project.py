"""Project Fair Share fetcher functions."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    ProjectFairShareConnection,
    ProjectFairShareEdge,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.fair_share.options import (
    ProjectFairShareConditions,
    ProjectFairShareOrders,
)
from ai.backend.manager.services.fair_share.actions import SearchProjectFairSharesAction


@lru_cache(maxsize=1)
def get_project_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ProjectFairShareOrders.by_created_at(ascending=False),
        backward_order=ProjectFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=ProjectFairShareConditions.by_cursor_forward,
        backward_condition_factory=ProjectFairShareConditions.by_cursor_backward,
    )


async def fetch_project_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: ProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ProjectFairShareConnection:
    """Fetch project fair shares with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., domain_name filter)
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
        get_project_fair_share_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processors.fair_share.search_project_fair_shares.wait_for_complete(
        SearchProjectFairSharesAction(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
    )

    nodes = [ProjectFairShareGQL.from_dataclass(data) for data in action_result.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
