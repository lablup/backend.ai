from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    EntityInvitationFilter,
    EntityInvitationOrderBy,
    EntityInvitationScopeDTO,
    ScopedSearchEntityInvitationsInput,
)
from ai.backend.common.dto.manager.v2.entity_invitation.types import EntityInvitationOrderField
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.entity_invitation.types import (
    CreateEntityInvitationInputGQL,
    EntityInvitationConnection,
    EntityInvitationEdge,
    EntityInvitationFilterGQL,
    EntityInvitationGQL,
    EntityInvitationOrderByGQL,
    EntityInvitationPayloadGQL,
    EntityInvitationScopeItemGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

_ADDED = "26.8.3"


@gql_root_field(
    BackendAIGQLMeta(
        added_version=_ADDED,
        description=(
            "Page through the invitations the named sides reach, combined with OR. "
            "RECEIVED and SENT are answered for by the caller and name nobody."
        ),
    )
)  # type: ignore[misc]
async def entity_invitations(
    info: Info[StrawberryGQLContext],
    scope: list[EntityInvitationScopeItemGQL],
    filter: EntityInvitationFilterGQL | None = None,
    order_by: list[EntityInvitationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityInvitationConnection | None:
    filter_dto: EntityInvitationFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[EntityInvitationOrderBy] | None = None
    if order_by:
        orders_dto = [
            EntityInvitationOrderBy(
                field=EntityInvitationOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]
    search_input = ScopedSearchEntityInvitationsInput(
        scope=EntityInvitationScopeDTO(items=[item.to_pydantic() for item in scope]),
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.entity_invitation.scoped_search(search_input)
    edges = [
        EntityInvitationEdge(
            node=EntityInvitationGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return EntityInvitationConnection(
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
        added_version=_ADDED,
        description=(
            "Read one invitation by id, from the side that offered it. "
            "The invitee reaches theirs through the search addressed to them."
        ),
    )
)  # type: ignore[misc]
async def entity_invitation(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityInvitationGQL | None:
    payload = await info.context.adapters.entity_invitation.get(EntityInvitationID(id))
    return EntityInvitationGQL.from_pydantic(payload.invitation)


@gql_mutation(
    BackendAIGQLMeta(added_version=_ADDED, description="Offer one entity to one address.")
)
async def create_entity_invitation(
    info: Info[StrawberryGQLContext],
    input: CreateEntityInvitationInputGQL,
) -> EntityInvitationPayloadGQL | None:
    payload = await info.context.adapters.entity_invitation.create(input.to_pydantic())
    return EntityInvitationPayloadGQL.from_pydantic(payload)


@gql_mutation(BackendAIGQLMeta(added_version=_ADDED, description="Take what was offered."))
async def accept_entity_invitation(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityInvitationPayloadGQL | None:
    payload = await info.context.adapters.entity_invitation.accept(EntityInvitationID(id))
    return EntityInvitationPayloadGQL.from_pydantic(payload)


@gql_mutation(BackendAIGQLMeta(added_version=_ADDED, description="Turn down what was offered."))
async def reject_entity_invitation(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityInvitationPayloadGQL | None:
    payload = await info.context.adapters.entity_invitation.reject(EntityInvitationID(id))
    return EntityInvitationPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=_ADDED, description="Withdraw an offer before it was answered.")
)
async def cancel_entity_invitation(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> EntityInvitationPayloadGQL | None:
    payload = await info.context.adapters.entity_invitation.cancel(EntityInvitationID(id))
    return EntityInvitationPayloadGQL.from_pydantic(payload)
