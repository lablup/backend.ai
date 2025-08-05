from typing import Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction


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


@strawberry.type
class CreateObjectStoragePayload:
    object_storage: ObjectStorage


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
