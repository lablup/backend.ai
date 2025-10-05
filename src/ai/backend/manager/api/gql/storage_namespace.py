from __future__ import annotations

import uuid
from typing import Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.object_storage_namespace.creator import StorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.register import (
    RegisterNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)

from .types import StrawberryGQLContext


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Storage namespace provides logical separation of data within a single storage system
    to organize and isolate domain-specific concerns.

    Implementation varies by storage type:
    - Object Storage (S3, MinIO): Uses bucket-based namespace separation
    - File System (VFS): Uses directory path prefix for namespace distinction
    """)
)
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


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Storage namespace connection for pagination.
    """)
)
class StorageNamespaceConnection(Connection[StorageNamespace]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for registering a storage namespace.
    """)
)
class RegisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace: str

    def to_creator(self) -> StorageNamespaceCreator:
        return StorageNamespaceCreator(
            storage_id=self.storage_id,
            bucket=self.namespace,
        )


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for unregistering a storage namespace.
    """)
)
class UnregisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace: str


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Payload returned after storage namespace registration.
    """)
)
class RegisterStorageNamespacePayload:
    id: uuid.UUID


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Payload returned after storage namespace unregistration.
    """)
)
class UnregisterStorageNamespacePayload:
    id: uuid.UUID


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Registers a new namespace within a storage.
    """)
)
async def register_storage_namespace(
    input: RegisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> RegisterStorageNamespacePayload:
    processors = info.context.processors

    action_result = await processors.storage_namespace.register.wait_for_complete(
        RegisterNamespaceAction(
            creator=input.to_creator(),
        )
    )

    return RegisterStorageNamespacePayload(id=action_result.storage_id)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Unregisters an existing namespace from a storage.
    """)
)
async def unregister_storage_namespace(
    input: UnregisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> UnregisterStorageNamespacePayload:
    processors = info.context.processors

    action_result = await processors.storage_namespace.unregister.wait_for_complete(
        UnregisterNamespaceAction(
            storage_id=input.storage_id,
            namespace=input.namespace,
        )
    )

    return UnregisterStorageNamespacePayload(id=action_result.storage_id)
