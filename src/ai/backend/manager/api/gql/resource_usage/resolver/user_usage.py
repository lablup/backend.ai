"""User Usage Bucket query resolvers."""

from __future__ import annotations

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
from ai.backend.manager.api.gql.types import ResourceGroupUserScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# Admin APIs


@strawberry.field(description="Added in 26.2.0. List user usage buckets (admin only).")  # type: ignore[misc]
async def admin_user_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: UserUsageBucketFilter | None = None,
    order_by: list[UserUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserUsageBucketConnection:
    """Search user usage buckets with pagination (admin only)."""
    check_admin_only()

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


# Resource Group Scoped APIs


@strawberry.field(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. List user usage buckets within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_user_usage_buckets(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupUserScope,
    filter: UserUsageBucketFilter | None = None,
    order_by: list[UserUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserUsageBucketConnection:
    """Search user usage buckets within resource group scope."""
    raise NotImplementedError("rg_user_usage_buckets is not yet implemented")


# Legacy APIs (deprecated)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.1.0. List user usage buckets (superadmin only).",
    deprecation_reason=(
        "Use admin_user_usage_buckets instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def user_usage_buckets(
    info: Info[StrawberryGQLContext],
    filter: UserUsageBucketFilter | None = None,
    order_by: list[UserUsageBucketOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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
