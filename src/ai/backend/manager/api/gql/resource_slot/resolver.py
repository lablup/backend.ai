"""Root query resolvers for resource slot type queries."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchResourceSlotTypesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .types import (
    ResourceSlotTypeConnectionGQL,
    ResourceSlotTypeEdgeGQL,
    ResourceSlotTypeFilterGQL,
    ResourceSlotTypeGQL,
    ResourceSlotTypeOrderByGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Returns a single resource slot type by slot_name, or null.",
    )
)  # type: ignore[misc]
async def resource_slot_type(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeGQL | None:
    node = await info.context.adapters.resource_slot.get_slot_type(slot_name)
    return ResourceSlotTypeGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Returns resource slot types with pagination and filtering.",
    )
)  # type: ignore[misc]
async def resource_slot_types(
    info: Info[StrawberryGQLContext],
    filter: ResourceSlotTypeFilterGQL | None = None,
    order_by: list[ResourceSlotTypeOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ResourceSlotTypeConnectionGQL:
    search_input = AdminSearchResourceSlotTypesInput(
        filter=filter.to_pydantic() if filter is not None else None,
        order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    payload = await info.context.adapters.resource_slot.search_slot_types(search_input)

    nodes = [ResourceSlotTypeGQL.from_pydantic(item) for item in payload.items]
    edges = [ResourceSlotTypeEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ResourceSlotTypeConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
