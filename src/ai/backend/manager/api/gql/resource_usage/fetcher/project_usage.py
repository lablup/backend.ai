"""Project Usage Bucket fetcher functions for nested connections."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.resource_usage.types import (
    ProjectUsageBucketConnection,
    ProjectUsageBucketEdge,
    ProjectUsageBucketFilter,
    ProjectUsageBucketGQL,
    ProjectUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.resource_usage_history.options import (
    ProjectUsageBucketConditions,
    ProjectUsageBucketOrders,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    ProjectUsageBucketSearchScope,
)
from ai.backend.manager.services.resource_usage.actions import (
    SearchProjectUsageBucketsAction,
    SearchScopedProjectUsageBucketsAction,
)


@lru_cache(maxsize=1)
def get_project_usage_bucket_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ProjectUsageBucketOrders.by_period_start(ascending=False),
        backward_order=ProjectUsageBucketOrders.by_period_start(ascending=True),
        forward_condition_factory=ProjectUsageBucketConditions.by_cursor_forward,
        backward_condition_factory=ProjectUsageBucketConditions.by_cursor_backward,
    )


async def fetch_project_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: ProjectUsageBucketFilter | None = None,
    order_by: list[ProjectUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ProjectUsageBucketConnection:
    """Fetch project usage buckets with optional filtering, ordering, and pagination.

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
        get_project_usage_bucket_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processors.resource_usage.search_project_usage_buckets.wait_for_complete(
        SearchProjectUsageBucketsAction(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
    )

    nodes = [ProjectUsageBucketGQL.from_dataclass(data) for data in action_result.items]
    edges = [
        ProjectUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return ProjectUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_rg_project_usage_buckets(
    info: Info[StrawberryGQLContext],
    scope: ProjectUsageBucketSearchScope,
    filter: ProjectUsageBucketFilter | None = None,
    order_by: list[ProjectUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ProjectUsageBucketConnection:
    """Fetch project usage buckets using resource group scope.

    Returns usage buckets within the specified scope.
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
        get_project_usage_bucket_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = (
        await processors.resource_usage.search_scoped_project_usage_buckets.wait_for_complete(
            SearchScopedProjectUsageBucketsAction(
                scope=scope,
                querier=querier,
            )
        )
    )

    nodes = [ProjectUsageBucketGQL.from_dataclass(data) for data in action_result.items]
    edges = [
        ProjectUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return ProjectUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
