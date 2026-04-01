"""GraphQL query and mutation resolvers for resource presets."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    CreateResourcePresetInputGQL,
    CreateResourcePresetPayloadGQL,
    DeleteResourcePresetPayloadGQL,
    ResourcePresetConnection,
    ResourcePresetEdge,
    ResourcePresetFilterGQL,
    ResourcePresetGQL,
    ResourcePresetOrderByGQL,
    UpdateResourcePresetInputGQL,
    UpdateResourcePresetPayloadGQL,
)

# Query fields


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List resource presets (admin only).",
    )
)  # type: ignore[misc]
async def admin_resource_presets_v2(
    info: Info[StrawberryGQLContext],
    filter: ResourcePresetFilterGQL | None = None,
    order_by: list[ResourcePresetOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourcePresetConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.resource_preset.search(
        AdminSearchResourcePresetsInput(
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

    nodes = [ResourcePresetGQL.from_pydantic(data) for data in payload.items]
    edges = [ResourcePresetEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourcePresetConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single resource preset by ID (admin only).",
    )
)  # type: ignore[misc]
async def admin_resource_preset_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> ResourcePresetGQL | None:
    check_admin_only()
    node = await info.context.adapters.resource_preset.get(id)
    return ResourcePresetGQL.from_pydantic(node)


# Mutation fields


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new resource preset (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_resource_preset_v2(
    info: Info[StrawberryGQLContext],
    input: CreateResourcePresetInputGQL,
) -> CreateResourcePresetPayloadGQL:
    check_admin_only()

    dto = input.to_pydantic()
    resource_slots = ResourceSlot({
        e.resource_type: Decimal(e.quantity) for e in dto.resource_slots
    })
    payload = await info.context.adapters.resource_preset.create(
        name=dto.name,
        resource_slots=resource_slots,
        shared_memory=dto.shared_memory.bytes if dto.shared_memory else None,
        resource_group_name=dto.resource_group_name,
    )
    return CreateResourcePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a resource preset (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_resource_preset_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateResourcePresetInputGQL,
) -> UpdateResourcePresetPayloadGQL:
    check_admin_only()

    dto = input.to_pydantic()
    payload = await info.context.adapters.resource_preset.update(dto)
    return UpdateResourcePresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a resource preset (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_resource_preset_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteResourcePresetPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_preset.delete(id)
    return DeleteResourcePresetPayloadGQL.from_pydantic(payload)
