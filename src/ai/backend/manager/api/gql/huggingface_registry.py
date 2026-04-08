from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    CreateHuggingFaceRegistryInput as CreateHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    DeleteHuggingFaceRegistryInput as DeleteHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    UpdateHuggingFaceRegistryInput as UpdateHuggingFaceRegistryInputDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    CreateHuggingFaceRegistryPayload as CreateHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    DeleteHuggingFaceRegistryPayload as DeleteHuggingFaceRegistryPayloadDTO,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    HuggingFaceRegistryNode,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    UpdateHuggingFaceRegistryPayload as UpdateHuggingFaceRegistryPayloadDTO,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_field,
    gql_mutation,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="HuggingFace registry node.",
    ),
)
class HuggingFaceRegistry(PydanticNodeMixin[HuggingFaceRegistryNode]):
    id: NodeID[str]
    url: str
    name: str
    token: str | None

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.huggingface_registry_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, registry_ids: Sequence[UUID]
    ) -> list[HuggingFaceRegistry]:
        nodes = await ctx.adapters.huggingface_registry.get_many(list(registry_ids))
        return [HuggingFaceRegistry.from_pydantic(node) for node in nodes]


HuggingFaceRegistryEdge = Edge[HuggingFaceRegistry]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated HuggingFace registry queries.",
    ),
)
class HuggingFaceRegistryConnection(Connection[HuggingFaceRegistry]):
    @gql_field(description="The count of this entity.")  # type: ignore[misc]
    def count(self) -> int:
        return len(self.edges)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="Get a HuggingFace registry by ID")
)  # type: ignore[misc]
async def huggingface_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> HuggingFaceRegistry | None:
    node = await info.context.adapters.huggingface_registry.get(UUID(id))
    return HuggingFaceRegistry.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="List all HuggingFace registries")
)  # type: ignore[misc]
async def huggingface_registries(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> HuggingFaceRegistryConnection | None:
    payload = await info.context.adapters.huggingface_registry.search(
        AdminSearchHuggingFaceRegistriesInput(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [HuggingFaceRegistry.from_pydantic(item) for item in payload.items]
    edges = [HuggingFaceRegistryEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return HuggingFaceRegistryConnection(
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
class CreateHuggingFaceRegistryInput(PydanticInputMixin[CreateHuggingFaceRegistryInputDTO]):
    name: str
    url: str
    token: str | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class UpdateHuggingFaceRegistryInput(PydanticInputMixin[UpdateHuggingFaceRegistryInputDTO]):
    id: ID
    url: str | None = UNSET
    name: str | None = UNSET
    token: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class DeleteHuggingFaceRegistryInput(PydanticInputMixin[DeleteHuggingFaceRegistryInputDTO]):
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating a HuggingFace registry.",
    ),
    model=CreateHuggingFaceRegistryPayloadDTO,
)
class CreateHuggingFaceRegistryPayload(PydanticOutputMixin[CreateHuggingFaceRegistryPayloadDTO]):
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating a HuggingFace registry.",
    ),
    model=UpdateHuggingFaceRegistryPayloadDTO,
)
class UpdateHuggingFaceRegistryPayload(PydanticOutputMixin[UpdateHuggingFaceRegistryPayloadDTO]):
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting a HuggingFace registry.",
    ),
    model=DeleteHuggingFaceRegistryPayloadDTO,
)
class DeleteHuggingFaceRegistryPayload(PydanticOutputMixin[DeleteHuggingFaceRegistryPayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted HuggingFace registry")


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Create huggingface registry."))  # type: ignore[misc]
async def create_huggingface_registry(
    input: CreateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateHuggingFaceRegistryPayload:
    result = await info.context.adapters.huggingface_registry.create(input.to_pydantic())
    return CreateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.huggingface_registry)
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Update huggingface registry."))  # type: ignore[misc]
async def update_huggingface_registry(
    input: UpdateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateHuggingFaceRegistryPayload:
    result = await info.context.adapters.huggingface_registry.update(input.to_pydantic())
    return UpdateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.huggingface_registry)
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Delete huggingface registry."))  # type: ignore[misc]
async def delete_huggingface_registry(
    input: DeleteHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteHuggingFaceRegistryPayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.huggingface_registry.delete(pydantic_input)
    return DeleteHuggingFaceRegistryPayload(id=result.id)
