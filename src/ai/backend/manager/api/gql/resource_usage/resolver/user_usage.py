"""User Usage Bucket query resolvers."""

from __future__ import annotations

from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.resource_usage.fetcher import fetch_user_usage_buckets
from ai.backend.manager.api.gql.resource_usage.types import (
    UserUsageBucketConnection,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(description="Added in 26.1.0. List user usage buckets (superadmin only).")
async def user_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: Optional[UserUsageBucketFilter] = None,
    order_by: Optional[list[UserUsageBucketOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> UserUsageBucketConnection:
    """Search user usage buckets with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access usage bucket data.")

    return await fetch_user_usage_buckets(
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
