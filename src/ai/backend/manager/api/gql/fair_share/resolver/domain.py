"""Domain Fair Share query resolvers."""

from __future__ import annotations

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
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightAction,
    DomainWeightInput,
    GetDomainFairShareAction,
    UpsertDomainFairShareWeightAction,
)

# Admin APIs


@strawberry.field(description="Added in 26.2.0. Get domain fair share data (admin only).")  # type: ignore[misc]
async def admin_domain_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    domain_name: str,
) -> DomainFairShareGQL | None:
    """Get a single domain fair share record (admin only)."""
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
        GetDomainFairShareAction(
            resource_group=resource_group,
            domain_name=domain_name,
        )
    )

    return DomainFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(description="Added in 26.2.0. List domain fair shares (admin only).")  # type: ignore[misc]
async def admin_domain_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: DomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainFairShareConnection:
    """Search domain fair shares with pagination (admin only)."""
    check_admin_only()

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


# Resource Group Scoped APIs


@strawberry.field(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Get domain fair share data within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_domain_fair_share(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    domain_name: str,
) -> DomainFairShareGQL | None:
    """Get a single domain fair share record within resource group scope."""
    raise NotImplementedError("rg_domain_fair_share is not yet implemented")


@strawberry.field(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. List domain fair shares within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_domain_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    filter: DomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainFairShareConnection:
    """Search domain fair shares within resource group scope."""
    raise NotImplementedError("rg_domain_fair_shares is not yet implemented")


# Legacy APIs (deprecated)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.1.0. Get domain fair share data (superadmin only).",
    deprecation_reason=(
        "Use admin_domain_fair_share instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def domain_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    domain_name: str,
) -> DomainFairShareGQL | None:
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

    return DomainFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.1.0. List domain fair shares (superadmin only).",
    deprecation_reason=(
        "Use admin_domain_fair_shares instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def domain_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: DomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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


# Admin Mutations


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Upsert domain fair share weight (admin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    )
)
async def admin_upsert_domain_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertDomainFairShareWeightInput,
) -> UpsertDomainFairShareWeightPayload:
    """Upsert domain fair share weight (admin only)."""
    check_admin_only()

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


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Bulk upsert domain fair share weights (admin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    )
)
async def admin_bulk_upsert_domain_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertDomainFairShareWeightInput,
) -> BulkUpsertDomainFairShareWeightPayload:
    """Bulk upsert domain fair share weights (admin only)."""
    check_admin_only()

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


# Legacy Mutations (deprecated)


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.1.0. Upsert domain fair share weight (superadmin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    ),
    deprecation_reason=(
        "Use admin_upsert_domain_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
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


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.1.0. Bulk upsert domain fair share weights (superadmin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    ),
    deprecation_reason=(
        "Use admin_bulk_upsert_domain_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
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
