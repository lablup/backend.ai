from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any, Self

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
    RegisterStorageNamespaceGQLPayload as RegisterStorageNamespaceGQLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    UnregisterStorageNamespacePayload as UnregisterStorageNamespacePayloadDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description=dedent_strip("""
            Storage namespace provides logical separation of data within a single storage system
            to organize and isolate domain-specific concerns.

            Implementation varies by storage type:
            - Object Storage (S3, MinIO): Uses bucket-based namespace separation
            - File System (VFS): Uses directory path prefix for namespace distinction
        """),
    ),
)
class StorageNamespace(PydanticNodeMixin[Any]):
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


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Storage namespace connection for pagination.",
    ),
)
class StorageNamespaceConnection(Connection[StorageNamespace]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input type for registering a storage namespace.",
        added_version="25.15.0",
    ),
    model=RegisterStorageNamespaceInputDTO,
)
class RegisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace: str

    def to_pydantic(self) -> RegisterStorageNamespaceInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return RegisterStorageNamespaceInputDTO(
            storage_id=self.storage_id,
            namespace=self.namespace,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input type for unregistering a storage namespace.",
        added_version="25.15.0",
    ),
    model=UnregisterStorageNamespaceInputDTO,
)
class UnregisterStorageNamespaceInput:
    storage_id: uuid.UUID
    namespace: str

    def to_pydantic(self) -> UnregisterStorageNamespaceInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return UnregisterStorageNamespaceInputDTO(
            storage_id=self.storage_id,
            namespace=self.namespace,
        )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Payload returned after storage namespace registration.",
    ),
    model=RegisterStorageNamespaceGQLPayloadDTO,
)
class RegisterStorageNamespacePayload:
    id: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Payload returned after storage namespace unregistration.",
    ),
    model=UnregisterStorageNamespacePayloadDTO,
)
class UnregisterStorageNamespacePayload:
    """Payload returned after storage namespace unregistration."""

    id: strawberry.auto


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
    return UnregisterStorageNamespacePayload(id=payload.id)
