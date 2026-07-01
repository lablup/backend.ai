"""GraphQL types for allocated resource slots on revisions and presets."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotFilter as AllocatedResourceSlotFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotOrder as AllocatedResourceSlotOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AllocatedResourceSlotNode as AllocatedResourceSlotNodeDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

# A resource slot row is bound to a single revision/preset and the slot count
# per parent is bounded by the number of declared resource slot types
# (CPU, MEM, GPU SKUs, …), which is small in practice. This limit effectively
# returns all rows without exposing cursor pagination on the field.
RESOURCE_SLOTS_FETCH_LIMIT = 10000


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


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Fields available for ordering allocated resource slots.",
    ),
    name="AllocatedResourceSlotOrderField",
)
class AllocatedResourceSlotOrderFieldGQL(StrEnum):
    SLOT_NAME = "slot_name"
    QUANTITY = "quantity"
    RANK = "rank"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for allocated resource slots.",
        added_version="26.4.2",
    ),
    name="AllocatedResourceSlotFilter",
)
class AllocatedResourceSlotFilterGQL(PydanticInputMixin[AllocatedResourceSlotFilterDTO]):
    slot_name: StringFilter | None = gql_field(default=None, description="Filter by slot name.")

    AND: list[Self] | None = gql_field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[Self] | None = gql_field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[Self] | None = gql_field(
        default=None, description="Logical NOT of filter conditions."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for allocated resource slots.",
        added_version="26.4.2",
    ),
    name="AllocatedResourceSlotOrderBy",
)
class AllocatedResourceSlotOrderByGQL(PydanticInputMixin[AllocatedResourceSlotOrderDTO]):
    field: AllocatedResourceSlotOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        default=OrderDirection.ASC, description="Order direction."
    )
