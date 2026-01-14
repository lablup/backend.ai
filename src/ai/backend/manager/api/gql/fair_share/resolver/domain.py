"""Domain Fair Share query resolvers."""

from __future__ import annotations

from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import fetch_domain_fair_shares
from ai.backend.manager.api.gql.fair_share.types import (
    DomainFairShareConnection,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.fair_share.actions import GetDomainFairShareAction


@strawberry.field(description="Added in 26.1.0. Get domain fair share data (superadmin only).")
async def domain_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    domain_name: str,
) -> Optional[DomainFairShareGQL]:
    """Get a single domain fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
        GetDomainFairShareAction(
            resource_group=resource_group,
            domain_name=domain_name,
        )
    )

    if action_result.data is None:
        return None
    return DomainFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(description="Added in 26.1.0. List domain fair shares (superadmin only).")
async def domain_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: Optional[DomainFairShareFilter] = None,
    order_by: Optional[list[DomainFairShareOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> DomainFairShareConnection:
    """Search domain fair shares with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    return await fetch_domain_fair_shares(
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
