"""Project Usage Bucket query resolvers."""

from __future__ import annotations

from typing import Optional

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
    filter: Optional[ProjectUsageBucketFilter] = None,
    order_by: Optional[list[ProjectUsageBucketOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
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
