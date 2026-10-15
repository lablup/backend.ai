from __future__ import annotations

from collections.abc import Iterable
from typing import Self, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    CreateVFSStorageInput as CreateVFSStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    DeleteVFSStorageInput as DeleteVFSStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    PartialBulkPurgeVFSStoragesInput as PartialBulkPurgeVFSStoragesInputDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    PartialBulkUpdateVFSStoragesInput as PartialBulkUpdateVFSStoragesInputDTO,
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
    PurgeVFSStoragePayload as PurgeVFSStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    UpdateVFSStoragePayload as UpdateVFSStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    VFSStorageNode,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, parse_uuid
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
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
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.9.0",
            description="UUID of the VFS storage.",
        ),
    )
    name: str
    host: str
    base_path: str

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.vfs_storage_loader.load_many([
            VFSStorageID(UUID(nid)) for nid in node_ids
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
    node = await info.context.adapters.vfs_storage.get(parse_uuid(id))
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several VFS storages, each answered for separately.",
    ),
    name="PartialBulkUpdateVFSStoragesInput",
)
class PartialBulkUpdateVFSStoragesInputGQL(
    PydanticInputMixin[PartialBulkUpdateVFSStoragesInputDTO]
):
    items: list[UpdateVFSStorageInput] = gql_field(
        description="The VFS storages to update, each with its ID and fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for permanently purging several VFS storages, each answered for separately."
        ),
    ),
    name="PartialBulkPurgeVFSStoragesInput",
)
class PartialBulkPurgeVFSStoragesInputGQL(PydanticInputMixin[PartialBulkPurgeVFSStoragesInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the VFS storages to purge.")


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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for VFS storage permanent purge.",
    ),
    model=PurgeVFSStoragePayloadDTO,
    name="PurgeVFSStoragePayload",
)
class PurgeVFSStoragePayloadGQL(PydanticOutputMixin[PurgeVFSStoragePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged VFS storage.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk VFS storage operation: the VFS storages processed and the "
            "ones that failed."
        ),
    ),
    model=PartialBulkPayload[VFSStorageNode],
    name="PartialBulkVFSStoragesPayload",
)
class PartialBulkVFSStoragesPayloadGQL(PydanticOutputMixin[PartialBulkPayload[VFSStorageNode]]):
    successes: list[VFSStorage] = gql_field(
        description="The VFS storages processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The VFS storages not processed, each with the reason."
    )


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Create a new VFS storage"),
    name="createVFSStorage",
)
async def create_vfs_storage(
    input: CreateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> CreateVFSStoragePayload | None:
    result = await info.context.adapters.vfs_storage.create(input.to_pydantic())
    return CreateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Update an existing VFS storage"),
    name="updateVFSStorage",
)
async def update_vfs_storage(
    input: UpdateVFSStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateVFSStoragePayload | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.vfs_storage.update(VFSStorageID(dto.id), dto)
    return UpdateVFSStoragePayload(vfs_storage=VFSStorage.from_pydantic(result.vfs_storage))


@gql_mutation(
    BackendAIGQLMeta(added_version="25.16.0", description="Delete a VFS storage"),
    name="deleteVFSStorage",
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeVFSStorage`.",
)
async def delete_vfs_storage(
    input: DeleteVFSStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteVFSStoragePayload | None:
    dto = input.to_pydantic()
    purged = await info.context.adapters.vfs_storage.purge(VFSStorageID(dto.id))
    return DeleteVFSStoragePayload.from_pydantic(DeleteVFSStoragePayloadDTO(id=purged.id))


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Permanently remove a VFS storage."
    ),
    name="purgeVFSStorage",
)
async def purge_vfs_storage(
    id: UUID, info: Info[StrawberryGQLContext]
) -> PurgeVFSStoragePayloadGQL:
    payload = await info.context.adapters.vfs_storage.purge(VFSStorageID(id))
    return PurgeVFSStoragePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several VFS storages, answering for each one.",
    ),
    name="partialBulkUpdateVFSStorages",
)
async def partial_bulk_update_vfs_storages(
    input: PartialBulkUpdateVFSStoragesInputGQL, info: Info[StrawberryGQLContext]
) -> PartialBulkVFSStoragesPayloadGQL:
    payload = await info.context.adapters.vfs_storage.partial_bulk_update(input.to_pydantic())
    return PartialBulkVFSStoragesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several VFS storages, answering for each one.",
    ),
    name="partialBulkPurgeVFSStorages",
)
async def partial_bulk_purge_vfs_storages(
    input: PartialBulkPurgeVFSStoragesInputGQL, info: Info[StrawberryGQLContext]
) -> PartialBulkVFSStoragesPayloadGQL:
    payload = await info.context.adapters.vfs_storage.partial_bulk_purge(input.to_pydantic())
    return PartialBulkVFSStoragesPayloadGQL.from_pydantic(payload)
