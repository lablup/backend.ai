from __future__ import annotations

import json
import uuid
from collections.abc import Iterable
from typing import Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.api_handlers import SENTINEL
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
    PresignedDownloadURLPayload as PresignedDownloadURLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    PresignedUploadURLPayload as PresignedUploadURLPayloadDTO,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.storage_namespace.actions.get_multi import (
    GetNamespacesAction,
)

from .storage_namespace import StorageNamespace, StorageNamespaceConnection, StorageNamespaceEdge
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.14.0")
class ObjectStorage(PydanticNodeMixin):
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
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: ObjectStorageData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            host=data.host,
            access_key=data.access_key,
            secret_key=data.secret_key,
            endpoint=data.endpoint,
            region=data.region or "",
        )

    @strawberry.field
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
        action_result = (
            await info.context.processors.storage_namespace.get_namespaces.wait_for_complete(
                GetNamespacesAction(uuid.UUID(self.id))
            )
        )

        nodes = [StorageNamespace.from_dataclass(bucket) for bucket in action_result.result]
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


@strawberry.type(description="Added in 25.14.0")
class ObjectStorageConnection(Connection[ObjectStorage]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
async def object_storage(id: ID, info: Info[StrawberryGQLContext]) -> ObjectStorage | None:
    node = await info.context.adapters.object_storage.get(uuid.UUID(id))
    return ObjectStorage.from_pydantic(node, extra={"region": node.region or ""})


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
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
        AdminSearchObjectStoragesInput(limit=limit, offset=offset)
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


@strawberry.experimental.pydantic.input(
    model=CreateObjectStorageInputDTO,
    description="Added in 25.14.0",
    all_fields=True,
)
class CreateObjectStorageInput:
    pass


@strawberry.experimental.pydantic.input(
    model=UpdateObjectStorageInputDTO,
    description="Added in 25.14.0",
)
class UpdateObjectStorageInput:
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    endpoint: str | None = UNSET
    region: str | None = UNSET

    def to_pydantic(self) -> UpdateObjectStorageInputDTO:
        return UpdateObjectStorageInputDTO(
            id=uuid.UUID(self.id),
            name=None if self.name is UNSET else self.name,
            host=None if self.host is UNSET else self.host,
            access_key=None if self.access_key is UNSET else self.access_key,
            secret_key=None if self.secret_key is UNSET else self.secret_key,
            endpoint=None if self.endpoint is UNSET else self.endpoint,
            region=SENTINEL if self.region is UNSET else self.region,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteObjectStorageInputDTO,
    description="Added in 25.14.0",
)
class DeleteObjectStorageInput:
    id: ID


@strawberry.experimental.pydantic.input(
    model=GetPresignedDownloadURLInputDTO,
    description="Added in 25.14.0",
)
class GetPresignedDownloadURLInput:
    artifact_revision_id: ID
    key: str
    expiration: int | None = None

    def to_pydantic(self) -> GetPresignedDownloadURLInputDTO:
        return GetPresignedDownloadURLInputDTO(
            artifact_revision_id=uuid.UUID(self.artifact_revision_id),
            key=self.key,
            expiration=self.expiration,
        )


@strawberry.experimental.pydantic.input(
    model=GetPresignedUploadURLInputDTO,
    description="Added in 25.14.0",
)
class GetPresignedUploadURLInput:
    artifact_revision_id: ID
    key: str

    def to_pydantic(self) -> GetPresignedUploadURLInputDTO:
        return GetPresignedUploadURLInputDTO(
            artifact_revision_id=uuid.UUID(self.artifact_revision_id),
            key=self.key,
        )


@strawberry.type(description="Added in 25.14.0")
class CreateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type(description="Added in 25.14.0")
class UpdateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type(description="Added in 25.14.0")
class DeleteObjectStoragePayload:
    id: ID


@strawberry.experimental.pydantic.type(
    model=PresignedDownloadURLPayloadDTO,
    name="GetPresignedDownloadURLPayload",
    description="Added in 25.14.0",
    all_fields=True,
)
class GetPresignedDownloadURLPayload:
    """Payload for presigned download URL generation result."""


@strawberry.experimental.pydantic.type(
    model=PresignedUploadURLPayloadDTO,
    name="GetPresignedUploadURLPayload",
    description="Added in 25.14.0",
    all_fields=True,
)
class GetPresignedUploadURLPayload:
    """Payload for presigned upload URL generation result."""


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload:
    result = await info.context.adapters.object_storage.create(input.to_pydantic())
    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    result = await info.context.adapters.object_storage.update(input.to_pydantic())
    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def delete_object_storage(
    input: DeleteObjectStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteObjectStoragePayload:
    pydantic_input = input.to_pydantic()
    result = await info.context.adapters.object_storage.delete(pydantic_input)
    return DeleteObjectStoragePayload(id=ID(str(result.id)))


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def get_presigned_download_url(
    input: GetPresignedDownloadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedDownloadURLPayload:
    processors = info.context.processors
    dto = input.to_pydantic()
    action_result = await processors.object_storage.get_presigned_download_url.wait_for_complete(
        GetDownloadPresignedURLAction(
            artifact_revision_id=dto.artifact_revision_id,
            key=dto.key,
            expiration=dto.expiration,
        )
    )

    return GetPresignedDownloadURLPayload.from_pydantic(
        PresignedDownloadURLPayloadDTO(presigned_url=action_result.presigned_url)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def get_presigned_upload_url(
    input: GetPresignedUploadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedUploadURLPayload:
    processors = info.context.processors
    dto = input.to_pydantic()
    action_result = await processors.object_storage.get_presigned_upload_url.wait_for_complete(
        GetUploadPresignedURLAction(
            artifact_revision_id=dto.artifact_revision_id,
            key=dto.key,
        )
    )

    return GetPresignedUploadURLPayload.from_pydantic(
        PresignedUploadURLPayloadDTO(
            presigned_url=action_result.presigned_url,
            fields=json.dumps(action_result.fields),
        )
    )
