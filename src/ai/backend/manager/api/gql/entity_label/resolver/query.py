"""Label GQL query resolvers."""

from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.entity_label.request import (
    EntityLabelFilter,
    EntityLabelOrder,
    SearchEntityLabelsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.entity.types.inputs import EntityTargetGQL
from ai.backend.manager.api.gql.entity_label.types import (
    EntityLabelConnection,
    EntityLabelEdge,
    EntityLabelFilterGQL,
    EntityLabelGQL,
    EntityLabelOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        description=(
            "Read the labels on the entities named. Scope items are OR'd, and naming an "
            "entity the caller cannot read refuses the whole read."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)  # type: ignore[misc]
async def entity_labels(
    info: Info[StrawberryGQLContext],
    scope: list[EntityTargetGQL],
    filter: EntityLabelFilterGQL | None = None,
    order_by: list[EntityLabelOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> EntityLabelConnection | None:
    filter_dto: EntityLabelFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[EntityLabelOrder] | None = (
        [o.to_pydantic() for o in order_by] if order_by else None
    )
    result = await info.context.adapters.entity_label.search(
        SearchEntityLabelsInput(
            scope=[s.to_pydantic() for s in scope],
            filter=filter_dto,
            order=orders_dto,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
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
