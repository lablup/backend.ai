from __future__ import annotations

from collections.abc import Iterable
from typing import Self, cast, override
from uuid import UUID

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
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
    PartialBulkPurgeObjectStoragesInput as PartialBulkPurgeObjectStoragesInputDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.request import (
    PartialBulkUpdateObjectStoragesInput as PartialBulkUpdateObjectStoragesInputDTO,
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
    PurgeObjectStoragePayload as PurgeObjectStoragePayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    UpdateObjectStoragePayload as UpdateObjectStoragePayloadDTO,
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
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.9.0",
            description="UUID of the object storage.",
        ),
    )
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.object_storage_loader.load_many([
            ObjectStorageID(UUID(nid)) for nid in node_ids
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
    ) -> StorageNamespaceConnection | None:
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
    node = await info.context.adapters.object_storage.get(parse_uuid(id))
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
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several object storages, each answered for separately.",
    ),
    name="PartialBulkUpdateObjectStoragesInput",
)
class PartialBulkUpdateObjectStoragesInputGQL(
    PydanticInputMixin[PartialBulkUpdateObjectStoragesInputDTO]
):
    items: list[UpdateObjectStorageInput] = gql_field(
        description="The object storages to update, each with its ID and fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for permanently purging several object storages, each answered for separately."
        ),
    ),
    name="PartialBulkPurgeObjectStoragesInput",
)
class PartialBulkPurgeObjectStoragesInputGQL(
    PydanticInputMixin[PartialBulkPurgeObjectStoragesInputDTO]
):
    ids: list[UUID] = gql_field(description="IDs of the object storages to purge.")


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
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for object storage permanent purge.",
    ),
    model=PurgeObjectStoragePayloadDTO,
    name="PurgeObjectStoragePayload",
)
class PurgeObjectStoragePayloadGQL(PydanticOutputMixin[PurgeObjectStoragePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged object storage.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk object storage operation: the object storages processed "
            "and the ones that failed."
        ),
    ),
    model=PartialBulkPayload[ObjectStorageNode],
    name="PartialBulkObjectStoragesPayload",
)
class PartialBulkObjectStoragesPayloadGQL(
    PydanticOutputMixin[PartialBulkPayload[ObjectStorageNode]]
):
    successes: list[ObjectStorage] = gql_field(
        description="The object storages processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The object storages not processed, each with the reason."
    )

    @classmethod
    def from_payload(
        cls, payload: PartialBulkPayload[ObjectStorageNode]
    ) -> PartialBulkObjectStoragesPayloadGQL:
        return cls(
            successes=[
                ObjectStorage.from_pydantic(node, extra={"region": node.region or ""})
                for node in payload.successes
            ],
            failed=[PartialBulkFailureGQL.from_pydantic(failure) for failure in payload.failed],
        )


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


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Create an object storage."))
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload | None:
    result = await info.context.adapters.object_storage.create(input.to_pydantic())
    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Update an object storage."))
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.object_storage.update(ObjectStorageID(dto.id), dto)
    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@gql_mutation(
    BackendAIGQLMeta(added_version="25.14.0", description="Delete an object storage."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeObjectStorage`.",
)
async def delete_object_storage(
    input: DeleteObjectStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteObjectStoragePayload | None:
    dto = input.to_pydantic()
    purged = await info.context.adapters.object_storage.purge(ObjectStorageID(dto.id))
    return DeleteObjectStoragePayload.from_pydantic(DeleteObjectStoragePayloadDTO(id=purged.id))


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Permanently remove an object storage."
    )
)
async def purge_object_storage(
    id: UUID, info: Info[StrawberryGQLContext]
) -> PurgeObjectStoragePayloadGQL:
    payload = await info.context.adapters.object_storage.purge(ObjectStorageID(id))
    return PurgeObjectStoragePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several object storages, answering for each one.",
    )
)
async def partial_bulk_update_object_storages(
    input: PartialBulkUpdateObjectStoragesInputGQL, info: Info[StrawberryGQLContext]
) -> PartialBulkObjectStoragesPayloadGQL:
    payload = await info.context.adapters.object_storage.partial_bulk_update(input.to_pydantic())
    return PartialBulkObjectStoragesPayloadGQL.from_payload(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several object storages, answering for each one.",
    )
)
async def partial_bulk_purge_object_storages(
    input: PartialBulkPurgeObjectStoragesInputGQL, info: Info[StrawberryGQLContext]
) -> PartialBulkObjectStoragesPayloadGQL:
    payload = await info.context.adapters.object_storage.partial_bulk_purge(input.to_pydantic())
    return PartialBulkObjectStoragesPayloadGQL.from_payload(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version="25.14.0", description="Get a presigned download URL.")
)
async def get_presigned_download_url(
    input: GetPresignedDownloadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedDownloadURLPayload | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.object_storage.get_presigned_download_url(
        artifact_revision_id=ArtifactRevisionID(dto.artifact_revision_id),
        key=dto.key,
        expiration=dto.expiration,
    )
    return GetPresignedDownloadURLPayload(presigned_url=result.presigned_url)


@gql_mutation(BackendAIGQLMeta(added_version="25.14.0", description="Get a presigned upload URL."))
async def get_presigned_upload_url(
    input: GetPresignedUploadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedUploadURLPayload | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.object_storage.get_presigned_upload_url(
        artifact_revision_id=ArtifactRevisionID(dto.artifact_revision_id),
        key=dto.key,
    )
    return GetPresignedUploadURLPayload(
        presigned_url=result.presigned_url,
        fields=result.fields,
    )
