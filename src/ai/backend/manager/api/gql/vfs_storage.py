from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Self

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
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.services.vfs_storage.actions.delete import DeleteVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction

from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.16.0. VFS Storage configuration")
class VFSStorage(PydanticNodeMixin):
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
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: VFSStorageData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            host=data.host,
            base_path=str(data.base_path),
        )


VFSStorageEdge = Edge[VFSStorage]


@strawberry.type(description="Added in 25.16.0. VFS Storage connection")
class VFSStorageConnection(Connection[VFSStorage]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.16.0. Get a VFS storage by ID")  # type: ignore[misc]
async def vfs_storage(id: ID, info: Info[StrawberryGQLContext]) -> VFSStorage | None:
    processors = info.context.processors
    action_result = await processors.vfs_storage.get.wait_for_complete(
        GetVFSStorageAction(storage_id=uuid.UUID(id))
    )
    return VFSStorage.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.16.0. List all VFS storages")  # type: ignore[misc]
async def vfs_storages(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFSStorageConnection | None:
    processors = info.context.processors

    action_result = await processors.vfs_storage.list_storages.wait_for_complete(
        ListVFSStorageAction()
    )

    nodes = [VFSStorage.from_dataclass(data) for data in action_result.data]
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


@strawberry.experimental.pydantic.input(
    model=CreateVFSStorageInputDTO,
    description="Added in 25.16.0. Input for creating VFS storage",
    all_fields=True,
)
class CreateVFSStorageInput:
    pass


@strawberry.experimental.pydantic.input(
    model=UpdateVFSStorageInputDTO,
    description="Added in 25.16.0. Input for updating VFS storage",
)
class UpdateVFSStorageInput:
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    base_path: str | None = UNSET

    def to_pydantic(self) -> UpdateVFSStorageInputDTO:
        return UpdateVFSStorageInputDTO(
            id=uuid.UUID(self.id),
            name=None if self.name is UNSET else self.name,
            host=None if self.host is UNSET else self.host,
            base_path=None if self.base_path is UNSET else self.base_path,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteVFSStorageInputDTO,
    description="Added in 25.16.0. Input for deleting VFS storage",
)
class DeleteVFSStorageInput:
    id: ID


@strawberry.type(description="Added in 25.16.0. Payload for creating VFS storage")
class CreateVFSStoragePayload:
    vfs_storage: VFSStorage


@strawberry.type(description="Added in 25.16.0. Payload for updating VFS storage")
class UpdateVFSStoragePayload:
    vfs_storage: VFSStorage


@strawberry.type(description="Added in 25.16.0. Payload for deleting VFS storage")
class DeleteVFSStoragePayload:
    id: ID


@strawberry.mutation(  # type: ignore[misc]
    name="createVFSStorage", description="Added in 25.16.0. Create a new VFS storage"
)
async def create_vfs_storage(
    input: CreateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> CreateVFSStoragePayload:
    result = await info.context.adapters.vfs_storage.create(input.to_pydantic())
    return CreateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@strawberry.mutation(  # type: ignore[misc]
    name="updateVFSStorage", description="Added in 25.16.0. Update an existing VFS storage"
)
async def update_vfs_storage(
    input: UpdateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateVFSStoragePayload:
    result = await info.context.adapters.vfs_storage.update(input.to_pydantic())
    return UpdateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@strawberry.mutation(name="deleteVFSStorage", description="Added in 25.16.0. Delete a VFS storage")  # type: ignore[misc]
async def delete_vfs_storage(
    input: DeleteVFSStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteVFSStoragePayload:
    processors = info.context.processors

    pydantic_input = input.to_pydantic()
    action_result = await processors.vfs_storage.delete.wait_for_complete(
        DeleteVFSStorageAction(
            storage_id=pydantic_input.id,
        )
    )

    return DeleteVFSStoragePayload(id=ID(str(action_result.deleted_storage_id)))
