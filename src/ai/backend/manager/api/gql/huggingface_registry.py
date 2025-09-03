from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.creator import HuggingFaceRegistryCreator
from ai.backend.manager.data.huggingface_registry.modifier import HuggingFaceRegistryModifier
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.services.artifact_registry.actions.huggingface.create import (
    CreateHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.delete import (
    DeleteHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
)

from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.14.0")
class HuggingFaceRegistry(Node):
    id: NodeID[str]
    url: str
    name: str
    token: Optional[str]

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
    ) -> list["HuggingFaceRegistry"]:
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


@strawberry.type(description="Added in 25.14.0")
class HuggingFaceRegistryConnection(Connection[HuggingFaceRegistry]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.14.0")
async def huggingface_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> Optional[HuggingFaceRegistry]:
    processors = info.context.processors
    action_result = await processors.artifact_registry.get_huggingface_registry.wait_for_complete(
        GetHuggingFaceRegistryAction(registry_id=uuid.UUID(id))
    )
    return HuggingFaceRegistry.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.14.0")
async def huggingface_registries(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> HuggingFaceRegistryConnection:
    # TODO: Support pagination with before, after, first, last
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = (
        await processors.artifact_registry.list_huggingface_registries.wait_for_complete(
            ListHuggingFaceRegistryAction()
        )
    )

    nodes = [HuggingFaceRegistry.from_dataclass(data) for data in action_result.data]
    edges = [
        HuggingFaceRegistryEdge(node=node, cursor=to_global_id(HuggingFaceRegistry, node.id))
        for node in nodes
    ]

    return HuggingFaceRegistryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input(description="Added in 25.14.0")
class CreateHuggingFaceRegistryInput:
    url: str
    name: str
    token: Optional[str] = None

    def to_creator(self) -> HuggingFaceRegistryCreator:
        return HuggingFaceRegistryCreator(url=self.url, token=self.token)

    def to_creator_meta(self) -> ArtifactRegistryCreatorMeta:
        return ArtifactRegistryCreatorMeta(name=self.name)


@strawberry.input(description="Added in 25.14.0")
class UpdateHuggingFaceRegistryInput:
    id: ID
    url: Optional[str] = UNSET
    name: Optional[str] = UNSET
    token: Optional[str] = UNSET

    def to_modifier(self) -> HuggingFaceRegistryModifier:
        return HuggingFaceRegistryModifier(
            url=OptionalState[str].from_graphql(self.url),
            token=OptionalState[str].from_graphql(self.token),
        )

    def to_modifier_meta(self) -> ArtifactRegistryModifierMeta:
        return ArtifactRegistryModifierMeta(
            name=OptionalState[str].from_graphql(self.name),
        )


@strawberry.input(description="Added in 25.14.0")
class DeleteHuggingFaceRegistryInput:
    id: ID


@strawberry.type(description="Added in 25.14.0")
class CreateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@strawberry.type(description="Added in 25.14.0")
class UpdateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@strawberry.type(description="Added in 25.14.0")
class DeleteHuggingFaceRegistryPayload:
    id: ID


@strawberry.mutation(description="Added in 25.14.0")
async def create_huggingface_registry(
    input: CreateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateHuggingFaceRegistryPayload:
    processors = info.context.processors

    action_result = (
        await processors.artifact_registry.create_huggingface_registry.wait_for_complete(
            CreateHuggingFaceRegistryAction(
                input.to_creator(),
                input.to_creator_meta(),
            )
        )
    )

    return CreateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def update_huggingface_registry(
    input: UpdateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateHuggingFaceRegistryPayload:
    processors = info.context.processors

    action_result = (
        await processors.artifact_registry.update_huggingface_registry.wait_for_complete(
            UpdateHuggingFaceRegistryAction(
                id=uuid.UUID(input.id), modifier=input.to_modifier(), meta=input.to_modifier_meta()
            )
        )
    )

    return UpdateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def delete_huggingface_registry(
    input: DeleteHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteHuggingFaceRegistryPayload:
    processors = info.context.processors

    await processors.artifact_registry.delete_huggingface_registry.wait_for_complete(
        DeleteHuggingFaceRegistryAction(registry_id=uuid.UUID(input.id))
    )

    return DeleteHuggingFaceRegistryPayload(id=input.id)
