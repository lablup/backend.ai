import uuid
from collections.abc import Sequence
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.artifact_registry_meta import ArtifactRegistryMetaConnection
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.reservoir_registry.creator import ReservoirRegistryCreator
from ai.backend.manager.data.reservoir_registry.modifier import ReservoirRegistryModifier
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.list import (
    ListReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
)

from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.14.0")
class ReservoirRegistry(Node):
    id: NodeID[str]
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @classmethod
    def from_dataclass(cls, data: ReservoirRegistryData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            endpoint=data.endpoint,
            access_key=data.access_key,
            secret_key=data.secret_key,
            api_version=data.api_version,
        )

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, reservoir_ids: Sequence[uuid.UUID]
    ) -> list["ReservoirRegistry"]:
        action_result = (
            await ctx.processors.artifact_registry.get_reservoir_registries.wait_for_complete(
                GetReservoirRegistriesAction(registry_ids=list(reservoir_ids))
            )
        )

        reservoirs = []
        for reservoir in action_result.result:
            reservoirs.append(ReservoirRegistry.from_dataclass(reservoir))

        return reservoirs

    @strawberry.field
    @classmethod
    async def remote_artifact_registries(
        cls, ctx: strawberry.Info[StrawberryGQLContext]
    ) -> ArtifactRegistryMetaConnection:
        raise NotImplementedAPI("This API is not implemented.")


ReservoirRegistryEdge = Edge[ReservoirRegistry]


@strawberry.type(description="Added in 25.14.0")
class ReservoirRegistryConnection(Connection[ReservoirRegistry]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.14.0")
async def reservoir_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> Optional[ReservoirRegistry]:
    processors = info.context.processors
    action_result = await processors.artifact_registry.get_reservoir_registry.wait_for_complete(
        GetReservoirRegistryAction(reservoir_id=uuid.UUID(id))
    )
    return ReservoirRegistry.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.14.0")
async def reservoir_registries(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> ReservoirRegistryConnection:
    # TODO: Support pagination with before, after, first, last
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = await processors.artifact_registry.list_reservoir_registries.wait_for_complete(
        ListReservoirRegistriesAction()
    )

    nodes = [ReservoirRegistry.from_dataclass(data) for data in action_result.data]
    edges = [
        ReservoirRegistryEdge(node=node, cursor=to_global_id(ReservoirRegistry, node.id))
        for node in nodes
    ]

    return ReservoirRegistryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input(description="Added in 25.14.0")
class CreateReservoirRegistryInput:
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    def to_creator(self) -> ReservoirRegistryCreator:
        return ReservoirRegistryCreator(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            api_version=self.api_version,
        )

    def to_creator_meta(self) -> ArtifactRegistryCreatorMeta:
        return ArtifactRegistryCreatorMeta(name=self.name)


@strawberry.input(description="Added in 25.14.0")
class UpdateReservoirRegistryInput:
    id: ID
    name: Optional[str] = UNSET
    endpoint: Optional[str] = UNSET
    access_key: Optional[str] = UNSET
    secret_key: Optional[str] = UNSET
    api_version: Optional[str] = UNSET

    def to_modifier(self) -> ReservoirRegistryModifier:
        return ReservoirRegistryModifier(
            endpoint=OptionalState[str].from_graphql(self.endpoint),
            access_key=OptionalState[str].from_graphql(self.access_key),
            secret_key=OptionalState[str].from_graphql(self.secret_key),
            api_version=OptionalState[str].from_graphql(self.api_version),
        )

    def to_modifier_meta(self) -> ArtifactRegistryModifierMeta:
        return ArtifactRegistryModifierMeta(
            name=OptionalState[str].from_graphql(self.name),
        )


@strawberry.input(description="Added in 25.14.0")
class DeleteReservoirRegistryInput:
    id: ID


@strawberry.type(description="Added in 25.14.0")
class CreateReservoirRegistryPayload:
    reservoir: ReservoirRegistry


@strawberry.type(description="Added in 25.14.0")
class UpdateReservoirRegistryPayload:
    reservoir: ReservoirRegistry


@strawberry.type(description="Added in 25.14.0")
class DeleteReservoirRegistryPayload:
    id: ID


@strawberry.mutation(description="Added in 25.14.0")
async def create_reservoir_registry(
    input: CreateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateReservoirRegistryPayload:
    processors = info.context.processors

    action_result = await processors.artifact_registry.create_reservoir_registry.wait_for_complete(
        CreateReservoirRegistryAction(
            input.to_creator(),
            input.to_creator_meta(),
        )
    )

    return CreateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def update_reservoir_registry(
    input: UpdateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateReservoirRegistryPayload:
    processors = info.context.processors

    action_result = await processors.artifact_registry.update_reservoir_registry.wait_for_complete(
        UpdateReservoirRegistryAction(
            id=uuid.UUID(input.id), modifier=input.to_modifier(), meta=input.to_modifier_meta()
        )
    )

    return UpdateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def delete_reservoir_registry(
    input: DeleteReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteReservoirRegistryPayload:
    processors = info.context.processors

    await processors.artifact_registry.delete_reservoir_registry.wait_for_complete(
        DeleteReservoirRegistryAction(reservoir_id=uuid.UUID(input.id))
    )

    return DeleteReservoirRegistryPayload(id=input.id)
