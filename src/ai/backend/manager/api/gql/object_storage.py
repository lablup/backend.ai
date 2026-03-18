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
    UpdateObjectStorageInput as UpdateObjectStorageInputDTO,
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


@strawberry.input(description="Added in 25.14.0")
class CreateObjectStorageInput:
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str


@strawberry.input(description="Added in 25.14.0")
class UpdateObjectStorageInput:
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    endpoint: str | None = UNSET
    region: str | None = UNSET


@strawberry.experimental.pydantic.input(
    model=DeleteObjectStorageInputDTO,
    description="Added in 25.14.0",
)
class DeleteObjectStorageInput:
    id: ID


@strawberry.input(description="Added in 25.14.0")
class GetPresignedDownloadURLInput:
    artifact_revision_id: ID
    key: str
    expiration: int | None = None


@strawberry.input(description="Added in 25.14.0")
class GetPresignedUploadURLInput:
    artifact_revision_id: ID
    key: str


@strawberry.type(description="Added in 25.14.0")
class CreateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type(description="Added in 25.14.0")
class UpdateObjectStoragePayload:
    object_storage: ObjectStorage


@strawberry.type(description="Added in 25.14.0")
class DeleteObjectStoragePayload:
    id: ID


@strawberry.type(description="Added in 25.14.0")
class GetPresignedDownloadURLPayload:
    presigned_url: str


@strawberry.type(description="Added in 25.14.0")
class GetPresignedUploadURLPayload:
    presigned_url: str
    fields: str  # JSON string containing the form fields


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload:
    result = await info.context.adapters.object_storage.create(
        CreateObjectStorageInputDTO(
            name=input.name,
            host=input.host,
            access_key=input.access_key,
            secret_key=input.secret_key,
            endpoint=input.endpoint,
            region=input.region,
        )
    )
    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_pydantic(
            result.object_storage, extra={"region": result.object_storage.region or ""}
        )
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    result = await info.context.adapters.object_storage.update(
        UpdateObjectStorageInputDTO(
            id=uuid.UUID(input.id),
            name=None if input.name is UNSET else input.name,
            host=None if input.host is UNSET else input.host,
            access_key=None if input.access_key is UNSET else input.access_key,
            secret_key=None if input.secret_key is UNSET else input.secret_key,
            endpoint=None if input.endpoint is UNSET else input.endpoint,
            region=SENTINEL if input.region is UNSET else input.region,
        )
    )
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

    action_result = await processors.object_storage.get_presigned_download_url.wait_for_complete(
        GetDownloadPresignedURLAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
            key=input.key,
            expiration=input.expiration,
        )
    )

    return GetPresignedDownloadURLPayload(presigned_url=action_result.presigned_url)


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def get_presigned_upload_url(
    input: GetPresignedUploadURLInput, info: Info[StrawberryGQLContext]
) -> GetPresignedUploadURLPayload:
    processors = info.context.processors

    action_result = await processors.object_storage.get_presigned_upload_url.wait_for_complete(
        GetUploadPresignedURLAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
            key=input.key,
        )
    )

    return GetPresignedUploadURLPayload(
        presigned_url=action_result.presigned_url, fields=json.dumps(action_result.fields)
    )
