from __future__ import annotations

import uuid
from typing import Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.data.object_storage_namespace.creator import ObjectStorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.object_storage.actions.register_bucket import RegisterBucketAction
from ai.backend.manager.services.object_storage.actions.unregister_bucket import (
    UnregisterBucketAction,
)

from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.15.0")
class StorageNamespace(Node):
    id: NodeID[str]
    storage_id: ID
    namespace: str

    @classmethod
    def from_dataclass(cls, data: StorageNamespaceData) -> Self:
        return cls(
            id=ID(str(data.id)),
            storage_id=ID(str(data.storage_id)),
            namespace=data.namespace,
        )


StorageNamespaceEdge = Edge[StorageNamespace]


@strawberry.type(description="Added in 25.15.0")
class StorageNamespaceConnection(Connection[StorageNamespace]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.input(description="Added in 25.15.0")
class RegisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace_name: str

    def to_creator(self) -> ObjectStorageNamespaceCreator:
        return ObjectStorageNamespaceCreator(
            storage_id=self.storage_id,
            bucket=self.namespace_name,
        )


@strawberry.input(description="Added in 25.15.0")
class UnregisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace_name: str


@strawberry.type(description="Added in 25.15.0")
class RegisterStorageNamespacePayload:
    id: uuid.UUID


@strawberry.type(description="Added in 25.15.0")
class UnregisterStorageNamespacePayload:
    id: uuid.UUID


@strawberry.mutation(description="Added in 25.15.0")
async def register_storage_namespace(
    input: RegisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> RegisterStorageNamespacePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.register_bucket.wait_for_complete(
        RegisterBucketAction(
            creator=input.to_creator(),
        )
    )

    return RegisterStorageNamespacePayload(id=action_result.storage_id)


@strawberry.mutation(description="Added in 25.15.0")
async def unregister_storage_namespace(
    input: UnregisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> UnregisterStorageNamespacePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.unregister_bucket.wait_for_complete(
        UnregisterBucketAction(
            storage_id=input.storage_id,
            bucket_name=input.namespace_name,
        )
    )

    return UnregisterStorageNamespacePayload(id=action_result.storage_id)
