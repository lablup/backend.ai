from __future__ import annotations

import uuid
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import to_global_id

from ...data.vfs_storage.types import VFSStorageData
from ...models.vfs_storage import VFSStorageRow
from ...repositories.base.creator import Creator
from ...repositories.base.updater import Updater
from ...repositories.vfs_storage import VFSStorageCreatorSpec
from ...repositories.vfs_storage.updaters import VFSStorageUpdaterSpec
from ...services.vfs_storage.actions.create import CreateVFSStorageAction
from ...services.vfs_storage.actions.delete import DeleteVFSStorageAction
from ...services.vfs_storage.actions.get import GetVFSStorageAction
from ...services.vfs_storage.actions.list import ListVFSStorageAction
from ...services.vfs_storage.actions.update import UpdateVFSStorageAction
from ...types import OptionalState
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.16.0. VFS Storage configuration")
class VFSStorage(Node):
    id: NodeID[str]
    name: str
    host: str
    base_path: str

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


@strawberry.field(description="Added in 25.16.0. Get a VFS storage by ID")
async def vfs_storage(id: ID, info: Info[StrawberryGQLContext]) -> Optional[VFSStorage]:
    processors = info.context.processors
    action_result = await processors.vfs_storage.get.wait_for_complete(
        GetVFSStorageAction(storage_id=uuid.UUID(id))
    )
    return VFSStorage.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.16.0. List all VFS storages")
async def vfs_storages(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> VFSStorageConnection:
    processors = info.context.processors

    action_result = await processors.vfs_storage.list_storages.wait_for_complete(
        ListVFSStorageAction()
    )

    nodes = [VFSStorage.from_dataclass(data) for data in action_result.data]
    edges = [VFSStorageEdge(node=node, cursor=to_global_id(VFSStorage, node.id)) for node in nodes]

    return VFSStorageConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.input(description="Added in 25.16.0. Input for creating VFS storage")
class CreateVFSStorageInput:
    name: str
    host: str
    base_path: str

    def to_creator(self) -> Creator[VFSStorageRow]:
        return Creator(
            spec=VFSStorageCreatorSpec(
                name=self.name,
                host=self.host,
                base_path=self.base_path,
            )
        )


@strawberry.input(description="Added in 25.16.0. Input for updating VFS storage")
class UpdateVFSStorageInput:
    id: ID
    name: Optional[str] = UNSET
    host: Optional[str] = UNSET
    base_path: Optional[str] = UNSET

    def to_updater(self) -> Updater[VFSStorageRow]:
        spec = VFSStorageUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            host=OptionalState[str].from_graphql(self.host),
            base_path=OptionalState[str].from_graphql(self.base_path),
        )
        return Updater(spec=spec, pk_value=uuid.UUID(self.id))


@strawberry.input(description="Added in 25.16.0. Input for deleting VFS storage")
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


@strawberry.mutation(
    name="createVFSStorage", description="Added in 25.16.0. Create a new VFS storage"
)
async def create_vfs_storage(
    input: CreateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> CreateVFSStoragePayload:
    processors = info.context.processors

    action_result = await processors.vfs_storage.create.wait_for_complete(
        CreateVFSStorageAction(
            creator=input.to_creator(),
        )
    )

    return CreateVFSStoragePayload(vfs_storage=VFSStorage.from_dataclass(action_result.result))


@strawberry.mutation(
    name="updateVFSStorage", description="Added in 25.16.0. Update an existing VFS storage"
)
async def update_vfs_storage(
    input: UpdateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateVFSStoragePayload:
    processors = info.context.processors

    action_result = await processors.vfs_storage.update.wait_for_complete(
        UpdateVFSStorageAction(
            updater=input.to_updater(),
        )
    )

    return UpdateVFSStoragePayload(vfs_storage=VFSStorage.from_dataclass(action_result.result))


@strawberry.mutation(name="deleteVFSStorage", description="Added in 25.16.0. Delete a VFS storage")
async def delete_vfs_storage(
    input: DeleteVFSStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteVFSStoragePayload:
    processors = info.context.processors

    action_result = await processors.vfs_storage.delete.wait_for_complete(
        DeleteVFSStorageAction(
            storage_id=uuid.UUID(input.id),
        )
    )

    return DeleteVFSStoragePayload(id=ID(str(action_result.deleted_storage_id)))
