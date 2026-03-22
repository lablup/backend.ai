"""Project Fair Share query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.fair_share.request import (
    GetProjectFairShareInput,
    SearchProjectFairSharesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertProjectFairShareWeightPayload,
    ProjectFairShareConnection,
    ProjectFairShareEdge,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    RGProjectFairShareFilter,
    UpsertProjectFairShareWeightInput,
    UpsertProjectFairShareWeightPayload,
)
from ai.backend.manager.api.gql.types import ResourceGroupProjectScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# Admin APIs


@strawberry.field(description="Added in 26.2.0. Get project fair share data (admin only).")  # type: ignore[misc]
async def admin_project_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    project_id: uuid.UUID,
) -> ProjectFairShareGQL | None:
    """Get a single project fair share record (admin only)."""
    check_admin_only()

    result = await info.context.adapters.fair_share.get_project(
        GetProjectFairShareInput(resource_group=resource_group_name, project_id=project_id)
    )
    return ProjectFairShareGQL.from_pydantic(result.item) if result.item is not None else None


@strawberry.field(description="Added in 26.2.0. List project fair shares (admin only).")  # type: ignore[misc]
async def admin_project_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: ProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection | None:
    """Search project fair shares with pagination (admin only)."""
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_project(
        SearchProjectFairSharesInput(
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

    nodes = [ProjectFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
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
    description="Added in 26.2.0. Get project fair share data within resource group scope."
)
async def rg_project_fair_share(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupProjectScope,
    project_id: uuid.UUID,
) -> ProjectFairShareGQL | None:
    """Get a single project fair share record within resource group scope."""
    result = await info.context.adapters.fair_share.get_project(
        GetProjectFairShareInput(resource_group=scope.resource_group_name, project_id=project_id)
    )
    return ProjectFairShareGQL.from_pydantic(result.item) if result.item is not None else None


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List project fair shares within resource group scope."
)
async def rg_project_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupProjectScope,
    filter: RGProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection | None:
    """Search project fair shares within resource group scope."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_rg_project(
        SearchProjectFairSharesInput(
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
        domain_name=scope.domain_name,
    )

    nodes = [ProjectFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
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
    description="Added in 26.1.0. Get project fair share data (superadmin only).",
    deprecation_reason=(
        "Use admin_project_fair_share instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def project_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    project_id: uuid.UUID,
) -> ProjectFairShareGQL | None:
    """Get a single project fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    result = await info.context.adapters.fair_share.get_project(
        GetProjectFairShareInput(resource_group=resource_group_name, project_id=project_id)
    )
    return ProjectFairShareGQL.from_pydantic(result.item) if result.item is not None else None


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.1.0. List project fair shares (superadmin only).",
    deprecation_reason=(
        "Use admin_project_fair_shares instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def project_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: ProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection | None:
    """Search project fair shares with pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.fair_share.search_project(
        SearchProjectFairSharesInput(
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

    nodes = [ProjectFairShareGQL.from_pydantic(item) for item in payload.items]
    edges = [ProjectFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ProjectFairShareConnection(
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
        "Added in 26.2.0. Upsert project fair share weight (admin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    )
)
async def admin_upsert_project_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertProjectFairShareWeightInput,
) -> UpsertProjectFairShareWeightPayload:
    """Upsert project fair share weight (admin only)."""
    check_admin_only()

    result = await info.context.adapters.fair_share.upsert_project(input.to_pydantic())
    return UpsertProjectFairShareWeightPayload(
        project_fair_share=ProjectFairShareGQL.from_pydantic(result.project_fair_share)
    )


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Bulk upsert project fair share weights (admin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    )
)
async def admin_bulk_upsert_project_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertProjectFairShareWeightInput,
) -> BulkUpsertProjectFairShareWeightPayload:
    """Bulk upsert project fair share weights (admin only)."""
    check_admin_only()

    result = await info.context.adapters.fair_share.bulk_upsert_project(input.to_pydantic())
    return BulkUpsertProjectFairShareWeightPayload.from_pydantic(result)


# Legacy Mutations (deprecated)


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.1.0. Upsert project fair share weight (superadmin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    ),
    deprecation_reason=(
        "Use admin_upsert_project_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def upsert_project_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertProjectFairShareWeightInput,
) -> UpsertProjectFairShareWeightPayload:
    """Upsert project fair share weight."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    result = await info.context.adapters.fair_share.upsert_project(input.to_pydantic())
    return UpsertProjectFairShareWeightPayload(
        project_fair_share=ProjectFairShareGQL.from_pydantic(result.project_fair_share)
    )


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.1.0. Bulk upsert project fair share weights (superadmin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    ),
    deprecation_reason=(
        "Use admin_bulk_upsert_project_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def bulk_upsert_project_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertProjectFairShareWeightInput,
) -> BulkUpsertProjectFairShareWeightPayload:
    """Bulk upsert project fair share weights."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    result = await info.context.adapters.fair_share.bulk_upsert_project(input.to_pydantic())
    return BulkUpsertProjectFairShareWeightPayload.from_pydantic(result)
