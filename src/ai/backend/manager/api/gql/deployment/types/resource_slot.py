"""GraphQL types for allocated resource slots on revisions and presets."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotFilter as AllocatedResourceSlotFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AllocatedResourceSlotOrder as AllocatedResourceSlotOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AllocatedResourceSlotNode as AllocatedResourceSlotNodeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Represents a single allocated resource slot entry for a deployment revision or preset.",
    ),
    name="AllocatedResourceSlot",
)
class AllocatedResourceSlotNodeGQL(PydanticNodeMixin[AllocatedResourceSlotNodeDTO]):
    id: NodeID[str]
    slot_name: str = gql_field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    quantity: Decimal = gql_field(description="Allocated quantity for this resource slot.")

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        raise NotImplementedError(
            "AllocatedResourceSlotNodeGQL is not a root-level entity and does not support resolve_nodes."
        )


AllocatedResourceSlotEdge = Edge[AllocatedResourceSlotNodeGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Connection type for paginated allocated resource slot results.",
    )
)
class AllocatedResourceSlotConnection(Connection[AllocatedResourceSlotNodeGQL]):
    count: int = gql_field(
        description="Total number of allocated resource slots matching the filter criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
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
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AllocatedResourceSlotFilter",
)
class AllocatedResourceSlotFilterGQL(PydanticInputMixin[AllocatedResourceSlotFilterDTO]):
    slot_name: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for allocated resource slots.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AllocatedResourceSlotOrderBy",
)
class AllocatedResourceSlotOrderByGQL(PydanticInputMixin[AllocatedResourceSlotOrderDTO]):
    field: AllocatedResourceSlotOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC
