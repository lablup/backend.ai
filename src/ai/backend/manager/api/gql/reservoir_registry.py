import uuid
from collections.abc import Iterable, Sequence
from typing import Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    CreateReservoirRegistryInput as CreateReservoirRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    DeleteReservoirRegistryInput as DeleteReservoirRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    UpdateReservoirRegistryInput as UpdateReservoirRegistryInputDTO,
)
from ai.backend.manager.api.gql.artifact_registry_meta import ArtifactRegistryMetaConnection
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
)

from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.14.0")
class ReservoirRegistry(PydanticNodeMixin):
    id: NodeID[str]
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.reservoir_registry_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

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


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
async def reservoir_registry(id: ID, info: Info[StrawberryGQLContext]) -> ReservoirRegistry | None:
    node = await info.context.adapters.reservoir_registry.get(uuid.UUID(id))
    return ReservoirRegistry.from_pydantic(node)


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
async def reservoir_registries(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> ReservoirRegistryConnection | None:
    payload = await info.context.adapters.reservoir_registry.search(
        AdminSearchReservoirRegistriesInput(limit=limit, offset=offset)
    )
    nodes = [ReservoirRegistry.from_pydantic(item) for item in payload.items]
    edges = [ReservoirRegistryEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ReservoirRegistryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.experimental.pydantic.input(
    model=CreateReservoirRegistryInputDTO,
    description="Added in 25.14.0",
    all_fields=True,
)
class CreateReservoirRegistryInput:
    pass


@strawberry.experimental.pydantic.input(
    model=UpdateReservoirRegistryInputDTO,
    description="Added in 25.14.0",
)
class UpdateReservoirRegistryInput:
    id: ID
    name: str | None = UNSET
    endpoint: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    api_version: str | None = UNSET

    def to_pydantic(self) -> UpdateReservoirRegistryInputDTO:
        return UpdateReservoirRegistryInputDTO(
            id=uuid.UUID(self.id),
            name=None if self.name is UNSET else self.name,
            endpoint=None if self.endpoint is UNSET else self.endpoint,
            access_key=None if self.access_key is UNSET else self.access_key,
            secret_key=None if self.secret_key is UNSET else self.secret_key,
            api_version=None if self.api_version is UNSET else self.api_version,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteReservoirRegistryInputDTO,
    description="Added in 25.14.0",
)
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


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def create_reservoir_registry(
    input: CreateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateReservoirRegistryPayload:
    result = await info.context.adapters.reservoir_registry.create(input.to_pydantic())
    return CreateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.registry)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_reservoir_registry(
    input: UpdateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateReservoirRegistryPayload:
    result = await info.context.adapters.reservoir_registry.update(input.to_pydantic())
    return UpdateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.registry)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def delete_reservoir_registry(
    input: DeleteReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteReservoirRegistryPayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.reservoir_registry.delete(pydantic_input)
    return DeleteReservoirRegistryPayload(id=ID(str(result.id)))
