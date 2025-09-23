from __future__ import annotations

import json
import uuid
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.storage_namespace.actions.get_multi import (
    GetNamespacesAction,
)

from ...data.object_storage.creator import ObjectStorageCreator
from ...data.object_storage.modifier import ObjectStorageModifier
from ...data.object_storage.types import ObjectStorageData
from ...services.object_storage.actions.create import CreateObjectStorageAction
from ...services.object_storage.actions.delete import DeleteObjectStorageAction
from ...services.object_storage.actions.get import GetObjectStorageAction
from ...services.object_storage.actions.list import ListObjectStorageAction
from ...services.object_storage.actions.update import UpdateObjectStorageAction
from ...types import OptionalState
from .storage_namespace import StorageNamespace, StorageNamespaceConnection, StorageNamespaceEdge
from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.14.0")
class ObjectStorage(Node):
    id: NodeID[str]
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @classmethod
    def from_dataclass(cls, data: ObjectStorageData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            host=data.host,
            access_key=data.access_key,
            secret_key=data.secret_key,
            endpoint=data.endpoint,
            region=data.region,
        )

    @strawberry.field
    async def namespaces(
        self,
        info: Info[StrawberryGQLContext],
        before: Optional[str],
        after: Optional[str],
        first: Optional[int],
        last: Optional[int],
        limit: Optional[int],
        offset: Optional[int],
    ) -> StorageNamespaceConnection:
        # TODO: Support pagination
        action_result = (
            await info.context.processors.storage_namespace.get_namespaces.wait_for_complete(
                GetNamespacesAction(uuid.UUID(self.id))
            )
        )

        nodes = [StorageNamespace.from_dataclass(bucket) for bucket in action_result.result]
        edges = [
            StorageNamespaceEdge(node=node, cursor=to_global_id(StorageNamespace, node.id))
            for node in nodes
        ]

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


@strawberry.field(description="Added in 25.14.0")
async def object_storage(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ObjectStorage]:
    processors = info.context.processors
    action_result = await processors.object_storage.get.wait_for_complete(
        GetObjectStorageAction(storage_id=uuid.UUID(id))
    )
    return ObjectStorage.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.14.0")
async def object_storages(
    info: Info[StrawberryGQLContext],
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ObjectStorageConnection:
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = await processors.object_storage.list_storages.wait_for_complete(
        ListObjectStorageAction()
    )

    nodes = [ObjectStorage.from_dataclass(data) for data in action_result.data]
    edges = [
        ObjectStorageEdge(node=node, cursor=to_global_id(ObjectStorage, node.id)) for node in nodes
    ]

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

    def to_creator(self) -> ObjectStorageCreator:
        return ObjectStorageCreator(
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region,
        )


@strawberry.input(description="Added in 25.14.0")
class UpdateObjectStorageInput:
    id: ID
    name: Optional[str] = UNSET
    host: Optional[str] = UNSET
    access_key: Optional[str] = UNSET
    secret_key: Optional[str] = UNSET
    endpoint: Optional[str] = UNSET
    region: Optional[str] = UNSET

    def to_modifier(self) -> ObjectStorageModifier:
        return ObjectStorageModifier(
            name=OptionalState[str].from_graphql(self.name),
            host=OptionalState[str].from_graphql(self.host),
            access_key=OptionalState[str].from_graphql(self.access_key),
            secret_key=OptionalState[str].from_graphql(self.secret_key),
            endpoint=OptionalState[str].from_graphql(self.endpoint),
            region=OptionalState[str].from_graphql(self.region),
        )


@strawberry.input(description="Added in 25.14.0")
class DeleteObjectStorageInput:
    id: ID


@strawberry.input(description="Added in 25.14.0")
class GetPresignedDownloadURLInput:
    artifact_revision_id: ID
    key: str
    expiration: Optional[int] = None


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


@strawberry.mutation(description="Added in 25.14.0")
async def create_object_storage(
    input: CreateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> CreateObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.create.wait_for_complete(
        CreateObjectStorageAction(
            creator=input.to_creator(),
        )
    )

    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.update.wait_for_complete(
        UpdateObjectStorageAction(
            id=uuid.UUID(input.id),
            modifier=input.to_modifier(),
        )
    )

    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")
async def delete_object_storage(
    input: DeleteObjectStorageInput, info: Info[StrawberryGQLContext]
) -> DeleteObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.delete.wait_for_complete(
        DeleteObjectStorageAction(
            storage_id=uuid.UUID(input.id),
        )
    )

    return DeleteObjectStoragePayload(id=ID(str(action_result.deleted_storage_id)))


@strawberry.mutation(description="Added in 25.14.0")
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


@strawberry.mutation(description="Added in 25.14.0")
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
