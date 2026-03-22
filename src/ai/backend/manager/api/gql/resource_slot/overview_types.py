"""GraphQL types for active resource overview."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.resource_slot.response import ActiveResourceOverviewInfoDTO
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_type
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.0",
        description=(
            "Active resource usage overview for a domain or project. "
            "Shows the currently occupied resource slots and the number of active sessions."
        ),
    ),
    model=ActiveResourceOverviewInfoDTO,
    name="ActiveResourceOverview",
)
class ActiveResourceOverviewGQL(PydanticOutputMixin[ActiveResourceOverviewInfoDTO]):
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
