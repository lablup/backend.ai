"""Project Fair Share query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import (
    fetch_project_fair_shares,
    fetch_rg_project_fair_shares,
)
from ai.backend.manager.api.gql.fair_share.types import (
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertProjectFairShareWeightPayload,
    ProjectFairShareConnection,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    UpsertProjectFairShareWeightInput,
    UpsertProjectFairShareWeightPayload,
)
from ai.backend.manager.api.gql.types import ResourceGroupProjectScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.repositories.fair_share.types import (
    ProjectFairShareSearchScope,
)
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertProjectFairShareWeightAction,
    GetProjectFairShareAction,
    ProjectWeightInput,
    UpsertProjectFairShareWeightAction,
)

# Admin APIs


@strawberry.field(description="Added in 26.2.0. Get project fair share data (admin only).")  # type: ignore[misc]
async def admin_project_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    project_id: uuid.UUID,
) -> ProjectFairShareGQL:
    """Get a single project fair share record (admin only)."""
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
        GetProjectFairShareAction(
            resource_group=resource_group_name,
            project_id=project_id,
        )
    )

    return ProjectFairShareGQL.from_dataclass(action_result.data)


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
) -> ProjectFairShareConnection:
    """Search project fair shares with pagination (admin only)."""
    check_admin_only()

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


# Resource Group Scoped APIs


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. Get project fair share data within resource group scope."
)
async def rg_project_fair_share(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupProjectScope,
    project_id: uuid.UUID,
) -> ProjectFairShareGQL:
    """Get a single project fair share record within resource group scope."""
    processors = info.context.processors
    action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
        GetProjectFairShareAction(
            resource_group=scope.resource_group_name,
            project_id=project_id,
        )
    )

    return ProjectFairShareGQL.from_dataclass(action_result.data)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List project fair shares within resource group scope."
)
async def rg_project_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupProjectScope,
    filter: ProjectFairShareFilter | None = None,
    order_by: list[ProjectFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ProjectFairShareConnection:
    """Search project fair shares within resource group scope."""
    repo_scope = ProjectFairShareSearchScope(
        resource_group=scope.resource_group_name,
        domain_name=scope.domain_name,
    )
    return await fetch_rg_project_fair_shares(
        info=info,
        scope=repo_scope,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
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
) -> ProjectFairShareGQL:
    """Get a single project fair share record."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
        GetProjectFairShareAction(
            resource_group=resource_group_name,
            project_id=project_id,
        )
    )

    return ProjectFairShareGQL.from_dataclass(action_result.data)


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

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_project_fair_share_weight.wait_for_complete(
        UpsertProjectFairShareWeightAction(
            resource_group=input.resource_group_name,
            project_id=input.project_id,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertProjectFairShareWeightPayload(
        project_fair_share=ProjectFairShareGQL.from_dataclass(action_result.data)
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

    processors = info.context.processors
    action_result = (
        await processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(
            BulkUpsertProjectFairShareWeightAction(
                resource_group=input.resource_group_name,
                inputs=[
                    ProjectWeightInput(
                        project_id=item.project_id,
                        domain_name=item.domain_name,
                        weight=item.weight,
                    )
                    for item in input.inputs
                ],
            )
        )
    )

    return BulkUpsertProjectFairShareWeightPayload(upserted_count=action_result.upserted_count)


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

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_project_fair_share_weight.wait_for_complete(
        UpsertProjectFairShareWeightAction(
            resource_group=input.resource_group_name,
            project_id=input.project_id,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertProjectFairShareWeightPayload(
        project_fair_share=ProjectFairShareGQL.from_dataclass(action_result.data)
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

    processors = info.context.processors
    action_result = (
        await processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(
            BulkUpsertProjectFairShareWeightAction(
                resource_group=input.resource_group_name,
                inputs=[
                    ProjectWeightInput(
                        project_id=item.project_id,
                        domain_name=item.domain_name,
                        weight=item.weight,
                    )
                    for item in input.inputs
                ],
            )
        )
    )

    return BulkUpsertProjectFairShareWeightPayload(upserted_count=action_result.upserted_count)
