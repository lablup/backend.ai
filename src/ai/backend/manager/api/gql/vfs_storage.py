from __future__ import annotations

from collections.abc import Iterable
from typing import Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    CreateVFSStorageInput as CreateVFSStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    DeleteVFSStorageInput as DeleteVFSStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    UpdateVFSStorageInput as UpdateVFSStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    CreateVFSStoragePayload as CreateVFSStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    DeleteVFSStoragePayload as DeleteVFSStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    UpdateVFSStoragePayload as UpdateVFSStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    VFSStorageNode,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_mutation,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)

from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="VFS Storage configuration.",
    ),
)
class VFSStorage(PydanticNodeMixin[VFSStorageNode]):
    id: NodeID[str]
    name: str
    host: str
    base_path: str

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.vfs_storage_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


VFSStorageEdge = Edge[VFSStorage]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="VFS Storage connection.",
    ),
)
class VFSStorageConnection(Connection[VFSStorage]):
    @gql_field(description="The count of this entity.")  # type: ignore[misc]
    def count(self) -> int:
        return len(self.edges)


@gql_root_field(BackendAIGQLMeta(added_version="25.16.0", description="Get a VFS storage by ID"))  # type: ignore[misc]
async def vfs_storage(id: ID, info: Info[StrawberryGQLContext]) -> VFSStorage | None:
    node = await info.context.adapters.vfs_storage.get(UUID(id))
    return VFSStorage.from_pydantic(node)


@gql_root_field(BackendAIGQLMeta(added_version="25.16.0", description="List all VFS storages"))  # type: ignore[misc]
async def vfs_storages(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFSStorageConnection | None:
    items = await info.context.adapters.vfs_storage.list_all()
    nodes = [VFSStorage.from_pydantic(item) for item in items]
    edges = [VFSStorageEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return VFSStorageConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for creating VFS storage", added_version="25.16.0"),
)
class CreateVFSStorageInput(PydanticInputMixin[CreateVFSStorageInputDTO]):
    name: str
    host: str
    base_path: str


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating VFS storage", added_version="25.16.0"),
)
class UpdateVFSStorageInput(PydanticInputMixin[UpdateVFSStorageInputDTO]):
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    base_path: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for deleting VFS storage", added_version="25.16.0"),
)
class DeleteVFSStorageInput(PydanticInputMixin[DeleteVFSStorageInputDTO]):
    id: ID


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload for creating VFS storage.",
    ),
    model=CreateVFSStoragePayloadDTO,
)
class CreateVFSStoragePayload:
    vfs_storage: VFSStorage


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload for updating VFS storage.",
    ),
    model=UpdateVFSStoragePayloadDTO,
)
class UpdateVFSStoragePayload:
    vfs_storage: VFSStorage


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload for deleting VFS storage.",
    ),
    model=DeleteVFSStoragePayloadDTO,
    name="DeleteVFSStoragePayload",
)
class DeleteVFSStoragePayload(PydanticOutputMixin[DeleteVFSStoragePayloadDTO]):
    """Payload for VFS storage deletion mutation."""

    id: UUID = gql_field(description="ID of the deleted VFS storage")


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Create a new VFS storage"),
    name="createVFSStorage",
)  # type: ignore[misc]
async def create_vfs_storage(
    input: CreateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> CreateVFSStoragePayload:
    result = await info.context.adapters.vfs_storage.create(input.to_pydantic())
    return CreateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Update an existing VFS storage"),
    name="updateVFSStorage",
)  # type: ignore[misc]
async def update_vfs_storage(
    input: UpdateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateVFSStoragePayload:
    result = await info.context.adapters.vfs_storage.update(input.to_pydantic())
    return UpdateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Delete a VFS storage"),
    name="deleteVFSStorage",
)  # type: ignore[misc]
async def delete_vfs_storage(
    input: DeleteVFSStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteVFSStoragePayload:
    result = await info.context.adapters.vfs_storage.delete(input.to_pydantic())
    return DeleteVFSStoragePayload.from_pydantic(result)
