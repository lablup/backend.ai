"""GraphQL query resolvers for resource group system."""

from __future__ import annotations

from typing import Any

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, PageInfo

from ai.backend.common.dto.manager.v2.resource_group.request import AdminSearchResourceGroupsInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_connection_type
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupFairShareSpecPayload,
    UpdateResourceGroupInput,
    UpdateResourceGroupPayload,
)

# Connection types

ResourceGroupEdge = Edge[ResourceGroupGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Resource group connection",
    )
)
class ResourceGroupConnection(Connection[ResourceGroupGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List resource groups (admin only)",
)
async def admin_resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [ResourceGroupGQL.from_pydantic(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. List resource groups",
    deprecation_reason=(
        "Use admin_resource_groups instead. This API will be removed after v26.3.0. "
        "See BEP-1041 for migration guide."
    ),
)
async def resource_groups(
    info: Info[StrawberryGQLContext],
    filter: ResourceGroupFilterGQL | None = None,
    order_by: list[ResourceGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceGroupConnection | None:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_group.search(
        AdminSearchResourceGroupsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [ResourceGroupGQL.from_pydantic(data) for data in payload.items]
    edges = [ResourceGroupEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


# Mutation fields


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update fair share configuration for a resource group (admin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Resource weights are validated against capacity - only resource types available in "
        "the scaling group's capacity can be specified."
    )
)
async def admin_update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    check_admin_only()

    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_fair_share_spec(dto)

    return UpdateResourceGroupFairShareSpecPayload.from_pydantic(payload_dto)


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update fair share configuration for a resource group (superadmin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Resource weights are validated against capacity - only resource types available in "
        "the scaling group's capacity can be specified."
    ),
    deprecation_reason=(
        "Use admin_update_resource_group_fair_share_spec instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def update_resource_group_fair_share_spec(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupFairShareSpecInput,
) -> UpdateResourceGroupFairShareSpecPayload:
    """Update fair share spec with partial update and validation."""
    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_fair_share_spec(dto)

    return UpdateResourceGroupFairShareSpecPayload.from_pydantic(payload_dto)


@strawberry.mutation(  # type: ignore[misc]
    description=(
        "Added in 26.2.0. Update resource group configuration (admin only). "
        "Only provided fields are updated; others retain their existing values. "
        "Supports all configuration fields except fair_share (use separate mutation)."
    )
)
async def admin_update_resource_group(
    info: Info[StrawberryGQLContext],
    input: UpdateResourceGroupInput,
) -> UpdateResourceGroupPayload:
    """Update resource group configuration with partial update."""
    check_admin_only()

    dto = input.to_pydantic()
    payload_dto = await info.context.adapters.resource_group.update_config(dto)

    return UpdateResourceGroupPayload.from_pydantic(payload_dto)
