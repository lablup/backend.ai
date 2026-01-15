"""User Fair Share query resolvers."""

from __future__ import annotations

import uuid
from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import fetch_user_fair_shares
from ai.backend.manager.api.gql.fair_share.types import (
    UserFairShareConnection,
    UserFairShareFilter,
    UserFairShareGQL,
    UserFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.fair_share.actions import GetUserFairShareAction


@strawberry.field(description="Added in 26.1.0. Get user fair share data (superadmin only).")
async def user_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    project_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> Optional[UserFairShareGQL]:
    """Get a single user fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
        GetUserFairShareAction(
            resource_group=resource_group,
            project_id=project_id,
            user_uuid=user_uuid,
        )
    )

    if action_result.data is None:
        return None
    return UserFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(description="Added in 26.1.0. List user fair shares (superadmin only).")
async def user_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: Optional[UserFairShareFilter] = None,
    order_by: Optional[list[UserFairShareOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> UserFairShareConnection:
    """Search user fair shares with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    return await fetch_user_fair_shares(
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
