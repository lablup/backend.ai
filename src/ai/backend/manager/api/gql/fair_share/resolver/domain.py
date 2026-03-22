"""Domain Fair Share query resolvers."""

from __future__ import annotations

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.fair_share.request import (
    GetDomainFairShareInput,
    SearchDomainFairSharesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertDomainFairShareWeightPayload,
    DomainFairShareConnection,
    DomainFairShareEdge,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
    RGDomainFairShareFilter,
    UpsertDomainFairShareWeightInput,
    UpsertDomainFairShareWeightPayload,
)
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# Admin APIs


@strawberry.field(description="Added in 26.2.0. Get domain fair share data (admin only).")  # type: ignore[misc]
async def admin_domain_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    domain_name: str,
) -> DomainFairShareGQL | None:
    """Get a single domain fair share record (admin only)."""
    check_admin_only()

    result = await info.context.adapters.fair_share.get_domain(
        GetDomainFairShareInput(resource_group=resource_group_name, domain_name=domain_name)
    )
    return DomainFairShareGQL.from_pydantic(result.item) if result.item is not None else None


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
) -> DomainFairShareConnection | None:
    """Search domain fair shares with pagination (admin only)."""
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_domain(
        SearchDomainFairSharesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [DomainFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [DomainFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


# Resource Group Scoped APIs


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. Get domain fair share data within resource group scope."
)
async def rg_domain_fair_share(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    domain_name: str,
) -> DomainFairShareGQL | None:
    """Get a single domain fair share record within resource group scope."""
    result = await info.context.adapters.fair_share.get_domain(
        GetDomainFairShareInput(resource_group=scope.resource_group_name, domain_name=domain_name)
    )
    return DomainFairShareGQL.from_pydantic(result.item) if result.item is not None else None


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List domain fair shares within resource group scope."
)
async def rg_domain_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupDomainScope,
    filter: RGDomainFairShareFilter | None = None,
    order_by: list[DomainFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DomainFairShareConnection | None:
    """Search domain fair shares within resource group scope."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_rg_domain(
        SearchDomainFairSharesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        resource_group=scope.resource_group_name,
    )

    nodes = [DomainFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [DomainFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


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
    resource_group_name: str,
    domain_name: str,
) -> DomainFairShareGQL | None:
    """Get a single domain fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    result = await info.context.adapters.fair_share.get_domain(
        GetDomainFairShareInput(resource_group=resource_group_name, domain_name=domain_name)
    )
    return DomainFairShareGQL.from_pydantic(result.item) if result.item is not None else None


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
) -> DomainFairShareConnection | None:
    """Search domain fair shares with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_domain(
        SearchDomainFairSharesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [DomainFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [DomainFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DomainFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(payload.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
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

    result = await info.context.adapters.fair_share.upsert_domain(input.to_pydantic())
    return UpsertDomainFairShareWeightPayload(
        domain_fair_share=DomainFairShareGQL.from_pydantic(result.domain_fair_share)
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

    result = await info.context.adapters.fair_share.bulk_upsert_domain(input.to_pydantic())
    return BulkUpsertDomainFairShareWeightPayload.from_pydantic(result)


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

    result = await info.context.adapters.fair_share.upsert_domain(input.to_pydantic())
    return UpsertDomainFairShareWeightPayload(
        domain_fair_share=DomainFairShareGQL.from_pydantic(result.domain_fair_share)
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

    result = await info.context.adapters.fair_share.bulk_upsert_domain(input.to_pydantic())
    return BulkUpsertDomainFairShareWeightPayload.from_pydantic(result)
