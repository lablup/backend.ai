from __future__ import annotations

import json
import uuid
from collections.abc import Iterable
from typing import Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.object_storage import ObjectStorageCreatorSpec
from ai.backend.manager.repositories.object_storage.updaters import ObjectStorageUpdaterSpec
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction
from ai.backend.manager.services.object_storage.actions.delete import DeleteObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get import GetObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.list import ListObjectStorageAction
from ai.backend.manager.services.object_storage.actions.update import UpdateObjectStorageAction
from ai.backend.manager.services.storage_namespace.actions.get_multi import (
    GetNamespacesAction,
)
from ai.backend.manager.types import OptionalState

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
    processors = info.context.processors
    action_result = await processors.object_storage.get.wait_for_complete(
        GetObjectStorageAction(storage_id=uuid.UUID(id))
    )
    return ObjectStorage.from_dataclass(action_result.result)


@strawberry.field(description="Added in 25.14.0")  # type: ignore[misc]
async def object_storages(
    info: Info[StrawberryGQLContext],
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ObjectStorageConnection:
    # TODO: Does we need to support filtering, ordering here?
    processors = info.context.processors

    action_result = await processors.object_storage.list_storages.wait_for_complete(
        ListObjectStorageAction()
    )

    nodes = [ObjectStorage.from_dataclass(data) for data in action_result.data]
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

    def to_creator(self) -> Creator[ObjectStorageRow]:
        return Creator(
            spec=ObjectStorageCreatorSpec(
                name=self.name,
                host=self.host,
                access_key=self.access_key,
                secret_key=self.secret_key,
                endpoint=self.endpoint,
                region=self.region,
            )
        )


@strawberry.input(description="Added in 25.14.0")
class UpdateObjectStorageInput:
    id: ID
    name: str | None = UNSET
    host: str | None = UNSET
    access_key: str | None = UNSET
    secret_key: str | None = UNSET
    endpoint: str | None = UNSET
    region: str | None = UNSET

    def to_updater(self) -> Updater[ObjectStorageRow]:
        spec = ObjectStorageUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            host=OptionalState[str].from_graphql(self.host),
            access_key=OptionalState[str].from_graphql(self.access_key),
            secret_key=OptionalState[str].from_graphql(self.secret_key),
            endpoint=OptionalState[str].from_graphql(self.endpoint),
            region=OptionalState[str].from_graphql(self.region),
        )
        return Updater(spec=spec, pk_value=uuid.UUID(self.id))


@strawberry.input(description="Added in 25.14.0")
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
    processors = info.context.processors

    action_result = await processors.object_storage.create.wait_for_complete(
        CreateObjectStorageAction(
            creator=input.to_creator(),
        )
    )

    return CreateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
async def update_object_storage(
    input: UpdateObjectStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateObjectStoragePayload:
    processors = info.context.processors

    action_result = await processors.object_storage.update.wait_for_complete(
        UpdateObjectStorageAction(
            updater=input.to_updater(),
        )
    )

    return UpdateObjectStoragePayload(
        object_storage=ObjectStorage.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.14.0")  # type: ignore[misc]
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
