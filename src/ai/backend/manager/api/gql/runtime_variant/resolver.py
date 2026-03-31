from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    RuntimeVariantFilter,
    RuntimeVariantOrder,
    SearchRuntimeVariantsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.runtime_variant.types import (
    CreateRuntimeVariantInputGQL,
    CreateRuntimeVariantPayloadGQL,
    DeleteRuntimeVariantPayloadGQL,
    RuntimeVariantConnection,
    RuntimeVariantEdge,
    RuntimeVariantFilterGQL,
    RuntimeVariantGQL,
    RuntimeVariantOrderByGQL,
    UpdateRuntimeVariantInputGQL,
    UpdateRuntimeVariantPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search runtime variants.",
    )
)  # type: ignore[misc]
async def runtime_variants(
    info: Info[StrawberryGQLContext],
    filter: RuntimeVariantFilterGQL | None = None,
    order_by: list[RuntimeVariantOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RuntimeVariantConnection | None:
    filter_dto: RuntimeVariantFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[RuntimeVariantOrder] | None = None
    if order_by:
        orders_dto = [
            RuntimeVariantOrder(
                field=RuntimeVariantOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]

    search_input = SearchRuntimeVariantsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    result = await info.context.adapters.runtime_variant.search(search_input)
    edges = [
        RuntimeVariantEdge(
            node=RuntimeVariantGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return RuntimeVariantConnection(
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
        description="Get a single runtime variant by ID.",
    )
)  # type: ignore[misc]
async def runtime_variant(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RuntimeVariantGQL | None:
    node = await info.context.adapters.runtime_variant.get(id)
    return RuntimeVariantGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new runtime variant (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_create_runtime_variant(
    info: Info[StrawberryGQLContext],
    input: CreateRuntimeVariantInputGQL,
) -> CreateRuntimeVariantPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.runtime_variant.create(dto)
    return CreateRuntimeVariantPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a runtime variant (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_update_runtime_variant(
    info: Info[StrawberryGQLContext],
    input: UpdateRuntimeVariantInputGQL,
) -> UpdateRuntimeVariantPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.runtime_variant.update(dto)
    return UpdateRuntimeVariantPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a runtime variant (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_delete_runtime_variant(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteRuntimeVariantPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.runtime_variant.delete(id)
    return DeleteRuntimeVariantPayloadGQL.from_pydantic(payload)
