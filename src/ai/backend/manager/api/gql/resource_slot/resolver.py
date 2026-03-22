"""Root query resolvers for resource slot type queries."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .fetcher import fetch_resource_slot_type, fetch_resource_slot_types
from .types import (
    ResourceSlotTypeConnectionGQL,
    ResourceSlotTypeFilterGQL,
    ResourceSlotTypeGQL,
    ResourceSlotTypeOrderByGQL,
)


@strawberry.field(
    description="Added in 26.3.0. Returns a single resource slot type by slot_name, or null."
)  # type: ignore[misc]
async def resource_slot_type(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeGQL | None:
    return await fetch_resource_slot_type(info, slot_name)


@strawberry.field(
    description="Added in 26.3.0. Returns resource slot types with pagination and filtering."
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
    return await fetch_resource_slot_types(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
