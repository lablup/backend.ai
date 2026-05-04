"""GraphQL types for allocated resource slots on revisions and presets."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AllocatedResourceSlotNode as AllocatedResourceSlotNodeDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="An allocated resource slot entry on a deployment revision or preset.",
    ),
    model=AllocatedResourceSlotNodeDTO,
    name="AllocatedResourceSlot",
)
class AllocatedResourceSlotGQL(PydanticOutputMixin[AllocatedResourceSlotNodeDTO]):
    slot_name: str = gql_field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    quantity: Decimal = gql_field(description="Allocated quantity for this resource slot.")
