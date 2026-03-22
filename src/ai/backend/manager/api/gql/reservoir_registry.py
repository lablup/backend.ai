import uuid
from collections.abc import Iterable, Sequence
from typing import Self, cast

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
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    CreateReservoirRegistryPayload as CreateReservoirRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    DeleteReservoirRegistryPayload as DeleteReservoirRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import ReservoirRegistryNode
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    UpdateReservoirRegistryPayload as UpdateReservoirRegistryPayloadDTO,
)
from ai.backend.manager.api.gql.artifact_registry_meta import ArtifactRegistryMetaConnection
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.errors.api import NotImplementedAPI

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Reservoir registry node.",
    ),
)
class ReservoirRegistry(PydanticNodeMixin[ReservoirRegistryNode]):
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
        return cast(list[Self | None], results)

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, reservoir_ids: Sequence[uuid.UUID]
    ) -> list["ReservoirRegistry"]:
        nodes = await ctx.adapters.reservoir_registry.get_many(list(reservoir_ids))
        return [ReservoirRegistry.from_pydantic(node) for node in nodes]

    @strawberry.field
    @classmethod
    async def remote_artifact_registries(
        cls, ctx: strawberry.Info[StrawberryGQLContext]
    ) -> ArtifactRegistryMetaConnection:
        raise NotImplementedAPI("This API is not implemented.")


ReservoirRegistryEdge = Edge[ReservoirRegistry]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated reservoir registry queries.",
    ),
)
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
        AdminSearchReservoirRegistriesInput(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class CreateReservoirRegistryInput(PydanticInputMixin[CreateReservoirRegistryInputDTO]):
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class UpdateReservoirRegistryInput(PydanticInputMixin[UpdateReservoirRegistryInputDTO]):
    id: ID
    name: str | None = UNSET
    endpoint: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    api_version: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class DeleteReservoirRegistryInput(PydanticInputMixin[DeleteReservoirRegistryInputDTO]):
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating a reservoir registry.",
    ),
    model=CreateReservoirRegistryPayloadDTO,
)
class CreateReservoirRegistryPayload(PydanticOutputMixin[CreateReservoirRegistryPayloadDTO]):
    reservoir: ReservoirRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating a reservoir registry.",
    ),
    model=UpdateReservoirRegistryPayloadDTO,
)
class UpdateReservoirRegistryPayload(PydanticOutputMixin[UpdateReservoirRegistryPayloadDTO]):
    reservoir: ReservoirRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting a reservoir registry.",
    ),
    model=DeleteReservoirRegistryPayloadDTO,
    fields=["id"],
)
class DeleteReservoirRegistryPayload(PydanticOutputMixin[DeleteReservoirRegistryPayloadDTO]):
    id: ID


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def create_reservoir_registry(
    input: CreateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateReservoirRegistryPayload:
    result = await info.context.adapters.reservoir_registry.create(input.to_pydantic())
    return CreateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.reservoir)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_reservoir_registry(
    input: UpdateReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateReservoirRegistryPayload:
    result = await info.context.adapters.reservoir_registry.update(input.to_pydantic())
    return UpdateReservoirRegistryPayload(
        reservoir=ReservoirRegistry.from_pydantic(result.reservoir)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def delete_reservoir_registry(
    input: DeleteReservoirRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteReservoirRegistryPayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.reservoir_registry.delete(pydantic_input)
    return DeleteReservoirRegistryPayload(id=ID(str(result.id)))
