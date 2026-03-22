"""Domain Usage Bucket query resolvers."""

from __future__ import annotations

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.resource_usage.types import (
    DomainUsageBucketConnection,
    DomainUsageBucketEdge,
    DomainUsageBucketFilter,
    DomainUsageBucketGQL,
    DomainUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# Admin APIs


@strawberry.field(description="Added in 26.2.0. List domain usage buckets (admin only).")  # type: ignore[misc]
async def admin_domain_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: DomainUsageBucketFilter | None = None,
    order_by: list[DomainUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainUsageBucketConnection | None:
    """Search domain usage buckets with pagination (admin only)."""
    check_admin_only()

    payload = await info.context.adapters.resource_usage.gql_admin_search_domain(
        filter=filter.to_pydantic() if filter else None,
        order=[o.to_pydantic() for o in order_by] if order_by else None,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    nodes = [DomainUsageBucketGQL.from_pydantic(item) for item in payload.items]
    edges = [DomainUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DomainUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


# Resource Group Scoped APIs


@strawberry.field(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. List domain usage buckets within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_domain_usage_buckets(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    filter: DomainUsageBucketFilter | None = None,
    order_by: list[DomainUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainUsageBucketConnection | None:
    """Search domain usage buckets within resource group scope."""
    raise NotImplementedError("rg_domain_usage_buckets is not yet implemented")


# Legacy APIs (deprecated)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.1.0. List domain usage buckets (superadmin only).",
    deprecation_reason=(
        "Use admin_domain_usage_buckets instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def domain_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: DomainUsageBucketFilter | None = None,
    order_by: list[DomainUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainUsageBucketConnection | None:
    """Search domain usage buckets with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access usage bucket data.")

    payload = await info.context.adapters.resource_usage.gql_admin_search_domain(
        filter=filter.to_pydantic() if filter else None,
        order=[o.to_pydantic() for o in order_by] if order_by else None,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    nodes = [DomainUsageBucketGQL.from_pydantic(item) for item in payload.items]
    edges = [DomainUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DomainUsageBucketConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
