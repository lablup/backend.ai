from __future__ import annotations

from collections.abc import Iterable
from typing import Self, cast
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    CreateObjectStorageInput as CreateObjectStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    DeleteObjectStorageInput as DeleteObjectStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    GetPresignedDownloadURLInput as GetPresignedDownloadURLInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    GetPresignedUploadURLInput as GetPresignedUploadURLInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    UpdateObjectStorageInput as UpdateObjectStorageInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    CreateObjectStoragePayload as CreateObjectStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    DeleteObjectStoragePayload as DeleteObjectStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    ObjectStorageNode,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    PresignedDownloadURLPayload as PresignedDownloadURLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    PresignedUploadURLPayload as PresignedUploadURLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    UpdateObjectStoragePayload as UpdateObjectStoragePayloadDTO,
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

from .storage_namespace import StorageNamespace, StorageNamespaceConnection, StorageNamespaceEdge
from .types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Object storage node.",
    ),
)
class ObjectStorage(PydanticNodeMixin[ObjectStorageNode]):
    id: NodeID[str]
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.object_storage_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)

    @gql_field(description="The namespaces of this entity.")  # type: ignore[misc]
    async def namespaces(
        self,
        info: Info[StrawberryGQLContext],
        before: str | None,
        after: str | None,
        first: int | None,
        last: int | None,
        limit: int | None,
        offset: int | None,
    ) -> StorageNamespaceConnection:
        # TODO: Support pagination
        items = await info.context.adapters.storage_namespace.get_namespaces(UUID(self.id))
        nodes = [StorageNamespace.from_pydantic(item) for item in items]
        edges = [StorageNamespaceEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

        return StorageNamespaceConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )


ObjectStorageEdge = Edge[ObjectStorage]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Relay-style connection for paginated object storage queries.",
    ),
)
class ObjectStorageConnection(Connection[ObjectStorage]):
    @gql_field(description="The count of this entity.")  # type: ignore[misc]
    def count(self) -> int:
        return len(self.edges)


@gql_root_field(
    BackendAIGQLMeta(added_version="25.14.0", description="Get an object storage by ID")
)  # type: ignore[misc]
async def object_storage(id: ID, info: Info[StrawberryGQLContext]) -> ObjectStorage | None:
    node = await info.context.adapters.object_storage.get(UUID(id))
    return ObjectStorage.from_pydantic(node, extra={"region": node.region or ""})


@gql_root_field(BackendAIGQLMeta(added_version="25.14.0", description="List all object storages"))  # type: ignore[misc]
async def object_storages(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ObjectStorageConnection | None:
    payload = await info.context.adapters.object_storage.admin_search(
        AdminSearchObjectStoragesInput(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [
        ObjectStorage.from_pydantic(item, extra={"region": item.region or ""})
        for item in payload.items
    ]
    edges = [ObjectStorageEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return ObjectStorageConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class CreateObjectStorageInput(PydanticInputMixin[CreateObjectStorageInputDTO]):
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class UpdateObjectStorageInput(PydanticInputMixin[UpdateObjectStorageInputDTO]):
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    endpoint: str | None = UNSET
    region: str | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class DeleteObjectStorageInput(PydanticInputMixin[DeleteObjectStorageInputDTO]):
    id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class GetPresignedDownloadURLInput(PydanticInputMixin[GetPresignedDownloadURLInputDTO]):
    artifact_revision_id: ID
    key: str
    expiration: int | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.14.0"),
)
class GetPresignedUploadURLInput(PydanticInputMixin[GetPresignedUploadURLInputDTO]):
    artifact_revision_id: ID
    key: str


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for creating an object storage.",
    ),
    model=CreateObjectStoragePayloadDTO,
)
class CreateObjectStoragePayload:
    object_storage: ObjectStorage


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for updating an object storage.",
    ),
    model=UpdateObjectStoragePayloadDTO,
)
class UpdateObjectStoragePayload:
    object_storage: ObjectStorage


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for deleting an object storage.",
    ),
    model=DeleteObjectStoragePayloadDTO,
    name="DeleteObjectStoragePayload",
)
class DeleteObjectStoragePayload(PydanticOutputMixin[DeleteObjectStoragePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted object storage.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for presigned download URL generation result.",
    ),
    model=PresignedDownloadURLPayloadDTO,
    name="GetPresignedDownloadURLPayload",
)
class GetPresignedDownloadURLPayload:
    """Payload for presigned download URL generation result."""

    presigned_url: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for presigned upload URL generation result.",
    ),
    model=PresignedUploadURLPayloadDTO,
    name="GetPresignedUploadURLPayload",
)
class GetPresignedUploadURLPayload:
    """Payload for presigned upload URL generation result."""

    presigned_url: strawberry.auto
    fields: strawberry.auto


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Create an object storage."))  # type: ignore[misc]
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload:
    result = await info.context.adapters.object_storage.create(input.to_pydantic())
    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Update an object storage."))  # type: ignore[misc]
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    result = await info.context.adapters.object_storage.update(input.to_pydantic())
    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Delete an object storage."))  # type: ignore[misc]
async def delete_object_storage(
    input: DeleteObjectStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteObjectStoragePayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.object_storage.delete(pydantic_input)
    return DeleteObjectStoragePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="25.14.0", description="Get a presigned download URL.")
)  # type: ignore[misc]
async def get_presigned_download_url(
    input: GetPresignedDownloadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedDownloadURLPayload:
    dto = input.to_pydantic()
    result = await info.context.adapters.object_storage.get_presigned_download_url(
        artifact_revision_id=dto.artifact_revision_id,
        key=dto.key,
        expiration=dto.expiration,
    )
    return GetPresignedDownloadURLPayload(presigned_url=result.presigned_url)


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Get a presigned upload URL."))  # type: ignore[misc]
async def get_presigned_upload_url(
    input: GetPresignedUploadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedUploadURLPayload:
    dto = input.to_pydantic()
    result = await info.context.adapters.object_storage.get_presigned_upload_url(
        artifact_revision_id=dto.artifact_revision_id,
        key=dto.key,
    )
    return GetPresignedUploadURLPayload(
        presigned_url=result.presigned_url,
        fields=result.fields,
    )
