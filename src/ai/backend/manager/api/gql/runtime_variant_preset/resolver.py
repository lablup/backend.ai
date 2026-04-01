from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetFilter,
    RuntimeVariantPresetOrder,
    SearchRuntimeVariantPresetsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    RuntimeVariantPresetOrderField,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.runtime_variant_preset.types import (
    CreateRuntimeVariantPresetInputGQL,
    CreateRuntimeVariantPresetPayloadGQL,
    DeleteRuntimeVariantPresetPayloadGQL,
    RuntimeVariantPresetConnection,
    RuntimeVariantPresetEdge,
    RuntimeVariantPresetFilterGQL,
    RuntimeVariantPresetGQL,
    RuntimeVariantPresetOrderByGQL,
    UpdateRuntimeVariantPresetInputGQL,
    UpdateRuntimeVariantPresetPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search runtime variant presets.",
    )
)  # type: ignore[misc]
async def runtime_variant_presets(
    info: Info[StrawberryGQLContext],
    filter: RuntimeVariantPresetFilterGQL | None = None,
    order_by: list[RuntimeVariantPresetOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RuntimeVariantPresetConnection | None:
    filter_dto: RuntimeVariantPresetFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[RuntimeVariantPresetOrder] | None = None
    if order_by:
        orders_dto = [
            RuntimeVariantPresetOrder(
                field=RuntimeVariantPresetOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]

    search_input = SearchRuntimeVariantPresetsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    result = await info.context.adapters.runtime_variant_preset.search(search_input)
    edges = [
        RuntimeVariantPresetEdge(
            node=RuntimeVariantPresetGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return RuntimeVariantPresetConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single runtime variant preset by ID.",
    )
)  # type: ignore[misc]
async def runtime_variant_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RuntimeVariantPresetGQL | None:
    node = await info.context.adapters.runtime_variant_preset.get(id)
    return RuntimeVariantPresetGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a runtime variant preset (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_create_runtime_variant_preset(
    info: Info[StrawberryGQLContext],
    input: CreateRuntimeVariantPresetInputGQL,
) -> CreateRuntimeVariantPresetPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.runtime_variant_preset.create(dto)
    return CreateRuntimeVariantPresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a runtime variant preset (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_update_runtime_variant_preset(
    info: Info[StrawberryGQLContext],
    input: UpdateRuntimeVariantPresetInputGQL,
) -> UpdateRuntimeVariantPresetPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.runtime_variant_preset.update(dto)
    return UpdateRuntimeVariantPresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a runtime variant preset (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_delete_runtime_variant_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteRuntimeVariantPresetPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.runtime_variant_preset.delete(id)
    return DeleteRuntimeVariantPresetPayloadGQL.from_pydantic(payload)
