"""Root query resolvers for resource slot type queries."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .fetcher import fetch_resource_slot_type, fetch_resource_slot_types
from .types import ResourceSlotTypeConnectionGQL, ResourceSlotTypeGQL


@strawberry.field(
    description="Added in 26.3.0. Returns a single resource slot type by slot_name, or null."
)  # type: ignore[misc]
async def resource_slot_type(
    info: Info[StrawberryGQLContext],
    slot_name: str,
) -> ResourceSlotTypeGQL | None:
    return await fetch_resource_slot_type(info, slot_name)


@strawberry.field(description="Added in 26.3.0. Returns all registered resource slot types.")  # type: ignore[misc]
async def resource_slot_types(
    info: Info[StrawberryGQLContext],
) -> ResourceSlotTypeConnectionGQL:
    return await fetch_resource_slot_types(info)
