from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardFilter,
    ModelCardOrder,
    SearchModelCardsInput,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardOrderField
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.model_card.types import (
    CreateModelCardInputGQL,
    CreateModelCardPayloadGQL,
    DeleteModelCardPayloadGQL,
    ModelCardFilterGQL,
    ModelCardGQL,
    ModelCardOrderByGQL,
    ModelCardV2Connection,
    ModelCardV2Edge,
    UpdateModelCardInputGQL,
    UpdateModelCardPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search model cards.",
    )
)  # type: ignore[misc]
async def model_cards_v2(
    info: Info[StrawberryGQLContext],
    filter: ModelCardFilterGQL | None = None,
    order_by: list[ModelCardOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelCardV2Connection | None:
    filter_dto: ModelCardFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[ModelCardOrder] | None = None
    if order_by:
        orders_dto = [
            ModelCardOrder(
                field=ModelCardOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]

    search_input = SearchModelCardsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    result = await info.context.adapters.model_card.search(search_input)
    edges = [
        ModelCardV2Edge(
            node=ModelCardGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return ModelCardV2Connection(
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
        description="Get a single model card by ID.",
    )
)  # type: ignore[misc]
async def model_card_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> ModelCardGQL | None:
    node = await info.context.adapters.model_card.get(id)
    return ModelCardGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_model_card_v2(
    info: Info[StrawberryGQLContext],
    input: CreateModelCardInputGQL,
) -> CreateModelCardPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.model_card.create(dto)
    return CreateModelCardPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_model_card_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateModelCardInputGQL,
) -> UpdateModelCardPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.model_card.update(dto)
    return UpdateModelCardPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_model_card_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteModelCardPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.model_card.delete(id)
    return DeleteModelCardPayloadGQL.from_pydantic(payload)
