"""The `entityLabels` connection field carried by every labelable entity."""

from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelOrder,
    EntityLabelPageInput,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .filters import EntityLabelFilterGQL, EntityLabelOrderByGQL
from .node import EntityLabelConnection, EntityLabelEdge, EntityLabelGQL

__all__ = ("resolve_entity_labels",)


async def resolve_entity_labels(
    info: Info[StrawberryGQLContext],
    owner: RuntimeEntityID,
    *,
    filter: EntityLabelFilterGQL | None,
    order_by: list[EntityLabelOrderByGQL] | None,
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    limit: int | None,
    offset: int | None,
) -> EntityLabelConnection:
    """Page the labels on one entity, which names itself as the owner."""
    filter_dto: EntityLabelFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[EntityLabelOrder] | None = (
        [o.to_pydantic() for o in order_by] if order_by else None
    )
    result = await info.context.adapters.entity_label.search_on(
        owner,
        EntityLabelPageInput(
            filter=filter_dto,
            order=orders_dto,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        EntityLabelEdge(
            node=EntityLabelGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return EntityLabelConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
