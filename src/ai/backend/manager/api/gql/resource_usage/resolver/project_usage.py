"""Project Usage Bucket query resolvers."""

from __future__ import annotations

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.resource_usage.fetcher import fetch_project_usage_buckets
from ai.backend.manager.api.gql.resource_usage.types import (
    ProjectUsageBucketConnection,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.1.0. List project usage buckets (superadmin only).")
async def project_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: ProjectUsageBucketFilter | None = None,
    order_by: list[ProjectUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectUsageBucketConnection:
    """Search project usage buckets with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access usage bucket data.")

    return await fetch_project_usage_buckets(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
