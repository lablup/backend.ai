from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from typing import Self

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
    gql_connection_type,
    gql_node_type,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
)

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
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: HuggingFaceRegistryData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            url=data.url,
            token=data.token,
        )

    @classmethod
    async def load_by_id(
        cls, ctx: StrawberryGQLContext, registry_ids: Sequence[uuid.UUID]
    ) -> list[HuggingFaceRegistry]:
        action_result = (
            await ctx.processors.artifact_registry.get_huggingface_registries.wait_for_complete(
                GetHuggingFaceRegistriesAction(registry_ids=list(registry_ids))
            )
        )

        registries = []
        for registry in action_result.result:
            registries.append(HuggingFaceRegistry.from_dataclass(registry))

        return registries


HuggingFaceRegistryEdge = Edge[HuggingFaceRegistry]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated HuggingFace registry queries.",
    ),
)
class HuggingFaceRegistryConnection(Connection[HuggingFaceRegistry]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
async def huggingface_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> HuggingFaceRegistry | None:
    node = await info.context.adapters.huggingface_registry.get(uuid.UUID(id))
    return HuggingFaceRegistry.from_pydantic(node)


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
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


@strawberry.experimental.pydantic.input(
    model=CreateHuggingFaceRegistryInputDTO,
    description="Added in 25.14.0",
    all_fields=True,
)
class CreateHuggingFaceRegistryInput:
    pass


@strawberry.experimental.pydantic.input(
    model=UpdateHuggingFaceRegistryInputDTO,
    description="Added in 25.14.0",
)
class UpdateHuggingFaceRegistryInput:
    id: ID
    url: str | None = UNSET
    name: str | None = UNSET
    token: str | None = UNSET

    def to_pydantic(self) -> UpdateHuggingFaceRegistryInputDTO:
        return UpdateHuggingFaceRegistryInputDTO(
            id=uuid.UUID(self.id),
            name=None if self.name is UNSET else self.name,
            url=None if self.url is UNSET else self.url,
            token=None if self.token is UNSET else self.token,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteHuggingFaceRegistryInputDTO,
    description="Added in 25.14.0",
)
class DeleteHuggingFaceRegistryInput:
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating a HuggingFace registry.",
    ),
    model=CreateHuggingFaceRegistryPayloadDTO,
)
class CreateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating a HuggingFace registry.",
    ),
    model=UpdateHuggingFaceRegistryPayloadDTO,
)
class UpdateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting a HuggingFace registry.",
    ),
    model=DeleteHuggingFaceRegistryPayloadDTO,
)
class DeleteHuggingFaceRegistryPayload:
    id: ID


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def create_huggingface_registry(
    input: CreateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateHuggingFaceRegistryPayload:
    result = await info.context.adapters.huggingface_registry.create(input.to_pydantic())
    return CreateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.registry)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_huggingface_registry(
    input: UpdateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateHuggingFaceRegistryPayload:
    result = await info.context.adapters.huggingface_registry.update(input.to_pydantic())
    return UpdateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_pydantic(result.registry)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def delete_huggingface_registry(
    input: DeleteHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteHuggingFaceRegistryPayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.huggingface_registry.delete(pydantic_input)
    return DeleteHuggingFaceRegistryPayload(id=ID(str(result.id)))
