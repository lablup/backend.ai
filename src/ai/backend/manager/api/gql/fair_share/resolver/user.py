"""User Fair Share query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from aiohttp import web
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.fair_share.fetcher import fetch_user_fair_shares
from ai.backend.manager.api.gql.fair_share.types import (
    BulkUpsertUserFairShareWeightInput,
    BulkUpsertUserFairShareWeightPayload,
    UpsertUserFairShareWeightInput,
    UpsertUserFairShareWeightPayload,
    UserFairShareConnection,
    UserFairShareFilter,
    UserFairShareGQL,
    UserFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import ResourceGroupUserScope, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertUserFairShareWeightAction,
    GetUserFairShareAction,
    UpsertUserFairShareWeightAction,
    UserWeightInput,
)

# Admin APIs


@strawberry.field(description="Added in 26.2.0. Get user fair share data (admin only).")
async def admin_user_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    project_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> UserFairShareGQL | None:
    """Get a single user fair share record (admin only)."""
    check_admin_only()

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


@strawberry.field(description="Added in 26.2.0. List user fair shares (admin only).")
async def admin_user_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: UserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserFairShareConnection:
    """Search user fair shares with pagination (admin only)."""
    check_admin_only()

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


# Resource Group Scoped APIs


@strawberry.field(
    description=(
        "Added in 26.2.0. Get user fair share data within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_user_fair_share(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupUserScope,
    user_uuid: uuid.UUID,
) -> UserFairShareGQL | None:
    """Get a single user fair share record within resource group scope."""
    raise NotImplementedError("rg_user_fair_share is not yet implemented")


@strawberry.field(
    description=(
        "Added in 26.2.0. List user fair shares within resource group scope. "
        "This API is not yet implemented."
    )
)
async def rg_user_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: ResourceGroupUserScope,
    filter: UserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserFairShareConnection:
    """Search user fair shares within resource group scope."""
    raise NotImplementedError("rg_user_fair_shares is not yet implemented")


# Legacy APIs (deprecated)


@strawberry.field(
    description="Added in 26.1.0. Get user fair share data (superadmin only).",
    deprecation_reason=(
        "Use admin_user_fair_share instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def user_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group: str,
    project_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> UserFairShareGQL | None:
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


@strawberry.field(
    description="Added in 26.1.0. List user fair shares (superadmin only).",
    deprecation_reason=(
        "Use admin_user_fair_shares instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def user_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: UserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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


# Admin Mutations


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Upsert user fair share weight (admin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    )
)
async def admin_upsert_user_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertUserFairShareWeightInput,
) -> UpsertUserFairShareWeightPayload:
    """Upsert user fair share weight (admin only)."""
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_user_fair_share_weight.wait_for_complete(
        UpsertUserFairShareWeightAction(
            resource_group=input.resource_group,
            project_id=input.project_id,
            user_uuid=input.user_uuid,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertUserFairShareWeightPayload(
        user_fair_share=UserFairShareGQL.from_dataclass(action_result.data)
    )


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Bulk upsert user fair share weights (admin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    )
)
async def admin_bulk_upsert_user_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertUserFairShareWeightInput,
) -> BulkUpsertUserFairShareWeightPayload:
    """Bulk upsert user fair share weights (admin only)."""
    check_admin_only()

    processors = info.context.processors
    action_result = (
        await processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(
            BulkUpsertUserFairShareWeightAction(
                resource_group=input.resource_group,
                inputs=[
                    UserWeightInput(
                        user_uuid=item.user_uuid,
                        project_id=item.project_id,
                        domain_name=item.domain_name,
                        weight=item.weight,
                    )
                    for item in input.inputs
                ],
            )
        )
    )

    return BulkUpsertUserFairShareWeightPayload(upserted_count=action_result.upserted_count)


# Legacy Mutations (deprecated)


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Upsert user fair share weight (superadmin only). "
        "Creates a new record if it doesn't exist, or updates the weight if it does."
    ),
    deprecation_reason=(
        "Use admin_upsert_user_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def upsert_user_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: UpsertUserFairShareWeightInput,
) -> UpsertUserFairShareWeightPayload:
    """Upsert user fair share weight."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    processors = info.context.processors
    action_result = await processors.fair_share.upsert_user_fair_share_weight.wait_for_complete(
        UpsertUserFairShareWeightAction(
            resource_group=input.resource_group,
            project_id=input.project_id,
            user_uuid=input.user_uuid,
            domain_name=input.domain_name,
            weight=input.weight,
        )
    )

    return UpsertUserFairShareWeightPayload(
        user_fair_share=UserFairShareGQL.from_dataclass(action_result.data)
    )


@strawberry.mutation(
    description=(
        "Added in 26.1.0. Bulk upsert user fair share weights (superadmin only). "
        "Creates new records if they don't exist, or updates weights if they do."
    ),
    deprecation_reason=(
        "Use admin_bulk_upsert_user_fair_share_weight instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def bulk_upsert_user_fair_share_weight(
    info: Info[StrawberryGQLContext],
    input: BulkUpsertUserFairShareWeightInput,
) -> BulkUpsertUserFairShareWeightPayload:
    """Bulk upsert user fair share weights."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can modify fair share data.")

    processors = info.context.processors
    action_result = (
        await processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(
            BulkUpsertUserFairShareWeightAction(
                resource_group=input.resource_group,
                inputs=[
                    UserWeightInput(
                        user_uuid=item.user_uuid,
                        project_id=item.project_id,
                        domain_name=item.domain_name,
                        weight=item.weight,
                    )
                    for item in input.inputs
                ],
            )
        )
    )

    return BulkUpsertUserFairShareWeightPayload(upserted_count=action_result.upserted_count)
