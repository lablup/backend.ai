import uuid
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.modifier import ObjectStorageModifier
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction
from ai.backend.manager.services.object_storage.actions.delete import DeleteObjectStorageAction
from ai.backend.manager.services.object_storage.actions.update import UpdateObjectStorageAction
from ai.backend.manager.types import OptionalState


@strawberry.type
class ObjectStorage(Node):
    id: NodeID[str]
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]

    @classmethod
    def from_dataclass(cls, image_data: ObjectStorageData) -> Self:
        return cls(
            id=ID(str(image_data.id)),  # TODO: Make this correct
            access_key=image_data.access_key,
            secret_key=image_data.secret_key,
            endpoint=image_data.endpoint,
            region=image_data.region,
            buckets=image_data.buckets,
        )


@strawberry.input
class CreateObjectStorageInput:
    name: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str
    buckets: list[str]

    def to_creator(self) -> ObjectStorageCreator:
        return ObjectStorageCreator(
            name=self.name,
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
    access_key: Optional[str] = UNSET
    secret_key: Optional[str] = UNSET
    endpoint: Optional[str] = UNSET
    region: Optional[str] = UNSET
    buckets: Optional[list[str]] = UNSET

    def to_modifier(self) -> ObjectStorageModifier:
        return ObjectStorageModifier(
            name=OptionalState[str].from_graphql(self.name),
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
