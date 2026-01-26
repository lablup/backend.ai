"""Domain Fair Share query resolvers."""

from __future__ import annotations

from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import fetch_domain_fair_shares
from ai.backend.manager.api.gql.fair_share.types import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertDomainFairShareWeightPayload,
    DomainFairShareConnection,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
    UpsertDomainFairShareWeightInput,
    UpsertDomainFairShareWeightPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightAction,
    DomainWeightInput,
    GetDomainFairShareAction,
    UpsertDomainFairShareWeightAction,
)


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


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Upsert domain fair share weight (superadmin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    )
)
async def upsert_domain_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertDomainFairShareWeightInput,
) -> UpsertDomainFairShareWeightPayload:
    """Upsert domain fair share weight."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_domain_fair_share_weight.wait_for_complete(
        UpsertDomainFairShareWeightAction(
            resource_group=input.resource_group,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertDomainFairShareWeightPayload(
        domain_fair_share=DomainFairShareGQL.from_dataclass(action_result.data)
    )


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Bulk upsert domain fair share weights (superadmin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    )
)
async def bulk_upsert_domain_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertDomainFairShareWeightInput,
) -> BulkUpsertDomainFairShareWeightPayload:
    """Bulk upsert domain fair share weights."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    processors = info.context.processors
    action_result = (
        await processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete(
            BulkUpsertDomainFairShareWeightAction(
                resource_group=input.resource_group,
                inputs=[
                    DomainWeightInput(
                        domain_name=item.domain_name,
                        weight=item.weight,
                    )
                    for item in input.inputs
                ],
            )
        )
    )

    return BulkUpsertDomainFairShareWeightPayload(upserted_count=action_result.upserted_count)
