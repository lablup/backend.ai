from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareFilter,
    EntityShareOrderBy,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareOrderField
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.entity_share.types import (
    CreateEntityShareInputGQL,
    EntityShareConnection,
    EntityShareEdge,
    EntityShareFilterGQL,
    EntityShareGQL,
    EntityShareOrderByGQL,
    EntitySharePayloadGQL,
    EntityShareScopeGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the invitations the named scopes reach, combined with OR. "
            "Every scope is authorized before the read runs."
        ),
    )
)  # type: ignore[misc]
async def entity_shares(
    info: Info[StrawberryGQLContext],
    scope: EntityShareScopeGQL,
    filter: EntityShareFilterGQL | None = None,
    order_by: list[EntityShareOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityShareConnection | None:
    filter_dto: EntityShareFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[EntityShareOrderBy] | None = None
    if order_by:
        orders_dto = [
            EntityShareOrderBy(
                field=EntityShareOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]
    search_input = ScopedSearchEntitySharesInput(
        scope=scope.to_pydantic(),
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.entity_share.scoped_search(search_input)
    edges = [
        EntityShareEdge(
            node=EntityShareGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return EntityShareConnection(
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
        description=(
            "Read one invitation by id, from the side that offered it. "
            "The invitee reaches theirs through the search addressed to them."
        ),
    )
)  # type: ignore[misc]
async def entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityShareGQL | None:
    payload = await info.context.adapters.entity_share.get(EntityShareID(id))
    return EntityShareGQL.from_pydantic(payload.invitation)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Offer one entity to one address."
    )
)
async def create_entity_share(
    info: Info[StrawberryGQLContext],
    input: CreateEntityShareInputGQL,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.create(input.to_pydantic())
    return EntitySharePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Take what was offered.")
)
async def accept_entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.accept(EntityShareID(id))
    return EntitySharePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Turn down what was offered.")
)
async def reject_entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.reject(EntityShareID(id))
    return EntitySharePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Withdraw an offer before it was answered."
    )
)
async def cancel_entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.cancel(EntityShareID(id))
    return EntitySharePayloadGQL.from_pydantic(payload)
