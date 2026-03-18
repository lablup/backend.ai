"""GraphQL types for active resource overview."""

from __future__ import annotations

from typing import Self

import strawberry

from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.data.resource_slot.types import ResourceOccupancy


@strawberry.type(
    name="ActiveResourceOverview",
    description=(
        "Added in 26.4.0. Active resource usage overview for a domain or project. "
        "Shows the currently occupied resource slots and the number of active sessions."
    ),
)
class ActiveResourceOverviewGQL:
    """Active resource occupancy for a domain or project."""

    slots: ResourceSlotGQL = strawberry.field(
        description=(
            "Resource slots currently occupied by active sessions. "
            "Each entry represents a resource type and the total quantity in use."
        )
    )
    session_count: int = strawberry.field(
        description="Number of active sessions contributing to the current resource occupancy."
    )

    @classmethod
    def from_occupancy(cls, occupancy: ResourceOccupancy) -> Self:
        """Convert a ResourceOccupancy data object to GraphQL type."""
        return cls(
            slots=ResourceSlotGQL.from_slot_quantities(occupancy.used_slots),
            session_count=occupancy.session_count,
        )
