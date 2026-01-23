"""Project Fair Share query resolvers."""

from __future__ import annotations

import uuid
from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import fetch_project_fair_shares
from ai.backend.manager.api.gql.fair_share.types import (
    ProjectFairShareConnection,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    UpsertProjectFairShareWeightInput,
    UpsertProjectFairShareWeightPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.fair_share.actions import (
    GetProjectFairShareAction,
    UpsertProjectFairShareWeightAction,
)


@strawberry.field(description="Added in 26.1.0. Get project fair share data (superadmin only).")
async def project_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    project_id: uuid.UUID,
) -> Optional[ProjectFairShareGQL]:
    """Get a single project fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
        GetProjectFairShareAction(
            resource_group=resource_group,
            project_id=project_id,
        )
    )

    if action_result.data is None:
        return None
    return ProjectFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(description="Added in 26.1.0. List project fair shares (superadmin only).")
async def project_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: Optional[ProjectFairShareFilter] = None,
    order_by: Optional[list[ProjectFairShareOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ProjectFairShareConnection:
    """Search project fair shares with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    return await fetch_project_fair_shares(
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


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Upsert project fair share weight (superadmin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    )
)
async def upsert_project_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertProjectFairShareWeightInput,
) -> UpsertProjectFairShareWeightPayload:
    """Upsert project fair share weight."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_project_fair_share_weight.wait_for_complete(
        UpsertProjectFairShareWeightAction(
            resource_group=input.resource_group,
            project_id=input.project_id,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertProjectFairShareWeightPayload(
        project_fair_share=ProjectFairShareGQL.from_dataclass(action_result.data)
    )
