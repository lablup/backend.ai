from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any, Self, cast

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
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.utils import dedent_strip

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
        return cast(list[Self | None], results)


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
)
class RegisterStorageNamespaceInput(PydanticInputMixin[RegisterStorageNamespaceInputDTO]):
    storage_id: uuid.UUID
    namespace: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input type for unregistering a storage namespace.",
        added_version="25.15.0",
    ),
)
class UnregisterStorageNamespaceInput(PydanticInputMixin[UnregisterStorageNamespaceInputDTO]):
    storage_id: uuid.UUID
    namespace: str


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
