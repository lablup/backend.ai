"""Domain Usage Bucket fetcher functions for nested connections."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.resource_usage.types import (
    DomainUsageBucketConnection,
    DomainUsageBucketEdge,
    DomainUsageBucketFilter,
    DomainUsageBucketGQL,
    DomainUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.resource_usage_history.options import (
    DomainUsageBucketConditions,
    DomainUsageBucketOrders,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    DomainUsageBucketSearchScope,
)
from ai.backend.manager.services.resource_usage.actions import (
    SearchDomainUsageBucketsAction,
    SearchScopedDomainUsageBucketsAction,
)


@lru_cache(maxsize=1)
def get_domain_usage_bucket_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DomainUsageBucketOrders.by_period_start(ascending=False),
        backward_order=DomainUsageBucketOrders.by_period_start(ascending=True),
        forward_condition_factory=DomainUsageBucketConditions.by_cursor_forward,
        backward_condition_factory=DomainUsageBucketConditions.by_cursor_backward,
    )


async def fetch_domain_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: DomainUsageBucketFilter | None = None,
    order_by: list[DomainUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> DomainUsageBucketConnection:
    """Fetch domain usage buckets with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., resource_group filter)
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
        get_domain_usage_bucket_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
        SearchDomainUsageBucketsAction(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
    )

    nodes = [DomainUsageBucketGQL.from_dataclass(data) for data in action_result.items]
    edges = [DomainUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_rg_domain_usage_buckets(
    info: Info[StrawberryGQLContext],
    scope: DomainUsageBucketSearchScope,
    filter: DomainUsageBucketFilter | None = None,
    order_by: list[DomainUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> DomainUsageBucketConnection:
    """Fetch domain usage buckets using resource group scope.

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
        get_domain_usage_bucket_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = (
        await processors.resource_usage.search_scoped_domain_usage_buckets.wait_for_complete(
            SearchScopedDomainUsageBucketsAction(
                scope=scope,
                querier=querier,
            )
        )
    )

    nodes = [DomainUsageBucketGQL.from_dataclass(data) for data in action_result.items]
    edges = [DomainUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
