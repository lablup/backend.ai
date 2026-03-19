from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    RegisterStorageNamespaceInput as RegisterStorageNamespaceInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    UnregisterStorageNamespaceInput as UnregisterStorageNamespaceInputDTO,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    UnregisterStorageNamespacePayload as UnregisterStorageNamespacePayloadDTO,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData

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
class StorageNamespace(PydanticNodeMixin):
    id: NodeID[str]
    storage_id: ID
    namespace: str

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.storage_namespace_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

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


@strawberry.experimental.pydantic.input(
    model=RegisterStorageNamespaceInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for registering a storage namespace.
    """),
    all_fields=True,
)
class RegisterStorageNamespaceInput:
    pass


@strawberry.experimental.pydantic.input(
    model=UnregisterStorageNamespaceInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for unregistering a storage namespace.
    """),
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


@strawberry.experimental.pydantic.type(
    model=UnregisterStorageNamespacePayloadDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Payload returned after storage namespace unregistration.
    """),
    all_fields=True,
)
class UnregisterStorageNamespacePayload:
    """Payload returned after storage namespace unregistration."""


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 25.15.0.

    Registers a new namespace within a storage.
    """)
)
async def register_storage_namespace(
    input: RegisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> RegisterStorageNamespacePayload:
    payload = await info.context.adapters.storage_namespace.register(input.to_pydantic())
    return RegisterStorageNamespacePayload(id=payload.namespace.storage_id)


@strawberry.mutation(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 25.15.0.

    Unregisters an existing namespace from a storage.
    """)
)
async def unregister_storage_namespace(
    input: UnregisterStorageNamespaceInput, info: Info[StrawberryGQLContext]
) -> UnregisterStorageNamespacePayload:
    pydantic_input = input.to_pydantic()
    payload = await info.context.adapters.storage_namespace.unregister(pydantic_input)
    return UnregisterStorageNamespacePayload.from_pydantic(payload)
