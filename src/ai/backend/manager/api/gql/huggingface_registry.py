import uuid
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

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
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
)

from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type
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


HuggingFaceRegistryEdge = Edge[HuggingFaceRegistry]


@strawberry.type
class HuggingFaceRegistryConnection(Connection[HuggingFaceRegistry]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field
async def huggingface_registry(
    id: ID, info: Info[StrawberryGQLContext]
) -> Optional[HuggingFaceRegistry]:
    processors = info.context.processors
    action_result = await processors.artifact_registry.get_huggingface_registry.wait_for_complete(
        GetHuggingFaceRegistryAction(registry_id=uuid.UUID(id))
    )
    return HuggingFaceRegistry.from_dataclass(action_result.result)


@strawberry.field
async def huggingface_registries(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
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
    edges = [HuggingFaceRegistryEdge(node=node, cursor=str(i)) for i, node in enumerate(nodes)]

    return HuggingFaceRegistryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input
class CreateHuggingFaceRegistryInput:
    url: str
    name: str
    token: Optional[str] = None

    def to_creator(self) -> HuggingFaceRegistryCreator:
        return HuggingFaceRegistryCreator(url=self.url, name=self.name, token=self.token)


@strawberry.input
class UpdateHuggingFaceRegistryInput:
    url: Optional[str] = UNSET
    name: Optional[str] = UNSET
    token: Optional[str] = UNSET

    def to_modifier(self) -> HuggingFaceRegistryModifier:
        return HuggingFaceRegistryModifier(
            name=OptionalState[str].from_graphql(self.name),
            url=OptionalState[str].from_graphql(self.url),
            token=OptionalState[str].from_graphql(self.token),
        )


@strawberry.input
class DeleteHuggingFaceRegistryInput:
    id: ID


@strawberry.type
class CreateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@strawberry.type
class UpdateHuggingFaceRegistryPayload:
    huggingface_registry: HuggingFaceRegistry


@strawberry.type
class DeleteHuggingFaceRegistryPayload:
    id: ID


@strawberry.mutation
async def create_huggingface_registry(
    input: CreateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> CreateHuggingFaceRegistryPayload:
    processors = info.context.processors

    action_result = (
        await processors.artifact_registry.create_huggingface_registry.wait_for_complete(
            CreateHuggingFaceRegistryAction(input.to_creator())
        )
    )

    return CreateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation
async def update_huggingface_registry(
    id: ID, input: UpdateHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> UpdateHuggingFaceRegistryPayload:
    processors = info.context.processors

    action_result = (
        await processors.artifact_registry.update_huggingface_registry.wait_for_complete(
            UpdateHuggingFaceRegistryAction(id=uuid.UUID(id), modifier=input.to_modifier())
        )
    )

    return UpdateHuggingFaceRegistryPayload(
        huggingface_registry=HuggingFaceRegistry.from_dataclass(action_result.result)
    )


@strawberry.mutation
async def delete_huggingface_registry(
    input: DeleteHuggingFaceRegistryInput, info: Info[StrawberryGQLContext]
) -> DeleteHuggingFaceRegistryPayload:
    processors = info.context.processors

    await processors.artifact_registry.delete_huggingface_registry.wait_for_complete(
        DeleteHuggingFaceRegistryAction(registry_id=uuid.UUID(input.id))
    )

    return DeleteHuggingFaceRegistryPayload(id=input.id)
