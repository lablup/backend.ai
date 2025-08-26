import uuid
from collections.abc import Sequence
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.data.reservoir.creator import ReservoirCreator
from ai.backend.manager.data.reservoir.modifier import ReservoirModifier
from ai.backend.manager.data.reservoir.types import ReservoirData
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.list import (
    ListReservoirAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirAction,
)

from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.13.0")
class Reservoir(Node):
    id: NodeID[str]
    name: str
    endpoint: str

    @classmethod
    def from_dataclass(cls, data: ReservoirData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            endpoint=data.endpoint,
        )

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, reservoir_ids: Sequence[uuid.UUID]
    ) -> list["Reservoir"]:
        reservoirs = []
        for reservoir_id in reservoir_ids:
            action_result = await ctx.processors.artifact_registry.get_reservoir.wait_for_complete(
                GetReservoirAction(reservoir_id=reservoir_id)
            )
            reservoirs.append(Reservoir.from_dataclass(action_result.result))
        return reservoirs


ReservoirEdge = Edge[Reservoir]


@strawberry.type(description="Added in 25.13.0")
class ReservoirConnection(Connection[Reservoir]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.13.0")
async def reservoir(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Reservoir]:
    processors = info.context.processors
    action_result = await processors.artifact_registry.get_reservoir.wait_for_complete(
        GetReservoirAction(reservoir_id=uuid.UUID(id))
    )
    return Reservoir.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.13.0")
async def reservoirs(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> ReservoirConnection:
    # TODO: Support pagination with before, after, first, last
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = await processors.artifact_registry.list_reservoirs.wait_for_complete(
        ListReservoirAction()
    )

    nodes = [Reservoir.from_dataclass(data) for data in action_result.data]
    edges = [ReservoirEdge(node=node, cursor=str(i)) for i, node in enumerate(nodes)]

    return ReservoirConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input(description="Added in 25.13.0")
class CreateReservoirInput:
    name: str
    endpoint: str

    def to_creator(self) -> ReservoirCreator:
        return ReservoirCreator(name=self.name, endpoint=self.endpoint)


@strawberry.input(description="Added in 25.13.0")
class UpdateReservoirInput:
    id: ID
    name: Optional[str] = UNSET
    endpoint: Optional[str] = UNSET

    def to_modifier(self) -> ReservoirModifier:
        return ReservoirModifier(
            name=OptionalState[str].from_graphql(self.name),
            endpoint=OptionalState[str].from_graphql(self.endpoint),
        )


@strawberry.input(description="Added in 25.13.0")
class DeleteReservoirInput:
    id: ID


@strawberry.type(description="Added in 25.13.0")
class CreateReservoirPayload:
    reservoir: Reservoir


@strawberry.type(description="Added in 25.13.0")
class UpdateReservoirPayload:
    reservoir: Reservoir


@strawberry.type(description="Added in 25.13.0")
class DeleteReservoirPayload:
    id: ID


@strawberry.mutation(description="Added in 25.13.0")
async def create_reservoir(
    input: CreateReservoirInput, info: Info[StrawberryGQLContext]
) -> CreateReservoirPayload:
    processors = info.context.processors

    action_result = await processors.artifact_registry.create_reservoir.wait_for_complete(
        CreateReservoirAction(input.to_creator())
    )

    return CreateReservoirPayload(reservoir=Reservoir.from_dataclass(action_result.result))


@strawberry.mutation(description="Added in 25.13.0")
async def update_reservoir(
    input: UpdateReservoirInput, info: Info[StrawberryGQLContext]
) -> UpdateReservoirPayload:
    processors = info.context.processors

    action_result = await processors.artifact_registry.update_reservoir.wait_for_complete(
        UpdateReservoirAction(id=uuid.UUID(input.id), modifier=input.to_modifier())
    )

    return UpdateReservoirPayload(reservoir=Reservoir.from_dataclass(action_result.result))


@strawberry.mutation(description="Added in 25.13.0")
async def delete_reservoir(
    input: DeleteReservoirInput, info: Info[StrawberryGQLContext]
) -> DeleteReservoirPayload:
    processors = info.context.processors

    await processors.artifact_registry.delete_reservoir.wait_for_complete(
        DeleteReservoirAction(reservoir_id=uuid.UUID(input.id))
    )

    return DeleteReservoirPayload(id=input.id)
