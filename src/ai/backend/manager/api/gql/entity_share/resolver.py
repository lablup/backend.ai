from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareOrderBy,
    MySearchEntitySharesInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.response import SearchEntitySharesPayload
from ai.backend.common.dto.manager.v2.entity_share.types import (
    EntityShareOrderField,
    EntityShareSideDTO,
)
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
    EntityShareSideGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the shares the caller stands on a side of. Naming no side reads both."
        ),
    )
)  # type: ignore[misc]
async def my_entity_shares(
    info: Info[StrawberryGQLContext],
    sides: list[EntityShareSideGQL] | None = None,
    filter: EntityShareFilterGQL | None = None,
    order_by: list[EntityShareOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityShareConnection | None:
    search_input = MySearchEntitySharesInput(
        sides=list(sides) if sides else [EntityShareSideDTO.RECIPIENT, EntityShareSideDTO.SHARER],
        filter=filter.to_pydantic() if filter else None,
        order=_to_orders(order_by),
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.entity_share.my_search(search_input)
    return _to_connection(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the shares the named scopes reach, combined with OR. "
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
    search_input = ScopedSearchEntitySharesInput(
        scope=scope.to_pydantic(),
        filter=filter.to_pydantic() if filter else None,
        order=_to_orders(order_by),
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.entity_share.scoped_search(search_input)
    return _to_connection(result)


def _to_orders(
    order_by: list[EntityShareOrderByGQL] | None,
) -> list[EntityShareOrderBy] | None:
    if not order_by:
        return None
    return [
        EntityShareOrderBy(
            field=EntityShareOrderField(o.field.value),
            direction=OrderDirection(o.direction),
        )
        for o in order_by
    ]


def _to_connection(result: SearchEntitySharesPayload) -> EntityShareConnection:
    edges = [
        EntityShareEdge(node=EntityShareGQL.from_pydantic(item), cursor=str(item.id))
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
            "Read one share by id, from the side that offered it. "
            "The receiving side reaches theirs through the search addressed to it."
        ),
    )
)  # type: ignore[misc]
async def entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityShareGQL | None:
    payload = await info.context.adapters.entity_share.get(EntityShareID(id))
    return EntityShareGQL.from_pydantic(payload.share)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Offer one entity to one project, one person, or one address.",
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


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Take back what was lent.")
)
async def revoke_entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.revoke(EntityShareID(id))
    return EntitySharePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Give back what was taken.")
)
async def leave_entity_share(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntitySharePayloadGQL | None:
    payload = await info.context.adapters.entity_share.leave(EntityShareID(id))
    return EntitySharePayloadGQL.from_pydantic(payload)
