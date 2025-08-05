import uuid
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ...data.object_storage.creator import ObjectStorageCreator
from ...data.object_storage.modifier import ObjectStorageModifier
from ...data.object_storage.types import ObjectStorageData
from ...services.object_storage.actions.create import CreateObjectStorageAction
from ...services.object_storage.actions.delete import DeleteObjectStorageAction
from ...services.object_storage.actions.get import GetObjectStorageAction
from ...services.object_storage.actions.list import ListObjectStorageAction
from ...services.object_storage.actions.update import UpdateObjectStorageAction
from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type
class ObjectStorage(Node):
    id: NodeID[str]
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]

    @classmethod
    def from_dataclass(cls, data: ObjectStorageData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            host=data.host,
            access_key=data.access_key,
            secret_key=data.secret_key,
            endpoint=data.endpoint,
            region=data.region,
            buckets=data.buckets,
        )


ObjectStorageEdge = Edge[ObjectStorage]


@strawberry.type
class ObjectStorageConnection(Connection[ObjectStorage]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field
async def object_storage(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ObjectStorage]:
    processors = info.context.processors
    action_result = await processors.object_storage.get.wait_for_complete(
        GetObjectStorageAction(storage_id=uuid.UUID(id))
    )
    return ObjectStorage.from_dataclass(action_result.result)


@strawberry.field
async def object_storages(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
) -> ObjectStorageConnection:
    # TODO: Support pagination with before, after, first, last
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = await processors.object_storage.list_.wait_for_complete(
        ListObjectStorageAction()
    )

    nodes = [ObjectStorage.from_dataclass(data) for data in action_result.data]
    edges = [ObjectStorageEdge(node=node, cursor=str(i)) for i, node in enumerate(nodes)]

    return ObjectStorageConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input
class CreateObjectStorageInput:
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]

    def to_creator(self) -> ObjectStorageCreator:
        return ObjectStorageCreator(
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region,
            buckets=self.buckets,
        )


@strawberry.input
class UpdateObjectStorageInput:
    id: ID
    name: Optional[str] = UNSET
    host: Optional[str] = UNSET
    access_key: Optional[str] = UNSET
    secret_key: Optional[str] = UNSET
    endpoint: Optional[str] = UNSET
    region: Optional[str] = UNSET
    buckets: Optional[list[str]] = UNSET

    def to_modifier(self) -> ObjectStorageModifier:
        return ObjectStorageModifier(
            name=OptionalState[str].from_graphql(self.name),
            host=OptionalState[str].from_graphql(self.host),
            access_key=OptionalState[str].from_graphql(self.access_key),
            secret_key=OptionalState[str].from_graphql(self.secret_key),
            endpoint=OptionalState[str].from_graphql(self.endpoint),
            region=OptionalState[str].from_graphql(self.region),
            buckets=OptionalState[list[str]].from_graphql(self.buckets),
        )


@strawberry.input
class DeleteObjectStorageInput:
    id: ID


@strawberry.type
class CreateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type
class UpdateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type
class DeleteObjectStoragePayload:
    id: ID


@strawberry.mutation
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.create.wait_for_complete(
        CreateObjectStorageAction(
            creator=input.to_creator(),
        )
    )

    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.update.wait_for_complete(
        UpdateObjectStorageAction(
            id=uuid.UUID(input.id),
            modifier=input.to_modifier(),
        )
    )

    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation
async def delete_object_storage(
    input: DeleteObjectStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.delete.wait_for_complete(
        DeleteObjectStorageAction(
            storage_id=uuid.UUID(input.id),
        )
    )

    return DeleteObjectStoragePayload(id=ID(str(action_result.deleted_storage_id)))
