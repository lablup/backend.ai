from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Optional, Self, Sequence

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.api.gql.base import ByteSize, OrderDirection, StringFilter
from ai.backend.manager.data.artifact.types import ArtifactStatus, ArtifactType


# Enums
@strawberry.enum
class ArtifactOrderField(StrEnum):
    ID = "ID"
    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    LATEST_VERSION = "LATEST_VERSION"


@strawberry.input
class ArtifactFilter:
    type: Optional[list[ArtifactType]] = None
    status: Optional[ArtifactStatusFilter] = None
    name: Optional[StringFilter] = None
    registry: Optional[StringFilter] = None
    source: Optional[StringFilter] = None

    AND: Optional["ArtifactFilter"] = None
    OR: Optional["ArtifactFilter"] = None
    NOT: Optional["ArtifactFilter"] = None
    DISTINCT: Optional[bool] = None


@strawberry.input
class ArtifactOrderBy:
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input
class ScanArtifactInput:
    registry_id: ID
    storage_id: ID
    limit: int
    search: Optional[str] = None


@strawberry.input
class ArtifactTarget:
    artifact_id: ID
    revision: str


@strawberry.input
class ImportArtifactsInput:
    artifacts: list[ArtifactTarget]
    storage_id: ID
    bucket_name: str


@strawberry.input
class UpdateArtifactInput:
    artifact_id: ID


@strawberry.input
class DeleteArtifactInput:
    artifact_id: ID


@strawberry.input
class AuthorizeArtifactInput:
    artifact_id: ID


@strawberry.input
class UnauthorizeArtifactInput:
    artifact_id: ID


@strawberry.input
class ArtifactStatusChangedInput:
    artifact_ids: list[ID]


# Object Types
@strawberry.type
class SourceInfo:
    name: Optional[str]
    url: Optional[str]


@strawberry.type
class Artifact(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    size: ByteSize

    @classmethod
    def from_dataclass(cls, data: ArtifactData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry=SourceInfo(name=None, url=None),
            source=SourceInfo(name=None, url=None),
            authorized=data.authorized,
        )

    @strawberry.field
    async def revisions(self, info: Info[StrawberryGQLContext]) -> ArtifactRevisionConnection:
        loader = info.context.dataloader_manager.get_loader_by_func(
            info.context, ArtifactRevision.batch_load_by_artifact_id
        )

        revision = await loader.load(self.id)
        edges = [ArtifactRevisionEdge(node=revision, cursor=str(revision.id))]

        return ArtifactRevisionConnection(
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            edges=edges,
        )

    @strawberry.field
    async def updated_at(self, info: Info[StrawberryGQLContext]) -> datetime:
        action_result = await info.context.processors.artifact.get_revisions.wait_for_complete(
            GetArtifactRevisionsAction(uuid.UUID(self.id))
        )

        return max(action_result.revisions, key=lambda r: r.updated_at).updated_at


@strawberry.type
class ArtifactRevision(Node):
    id: NodeID[str]
    status: ArtifactStatus
    created_at: datetime
    updated_at: datetime
    readme: str
    version: str
    size: ByteSize

    @classmethod
    def from_dataclass(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            status=ArtifactStatus(data.status),
            created_at=data.created_at,
            updated_at=data.updated_at,
            readme=data.readme,
            version=data.version,
            size=ByteSize(data.size),
        )

    @classmethod
    async def batch_load_by_artifact_id(
        cls, ctx: StrawberryGQLContext, artifact_ids: Sequence[uuid.UUID]
    ) -> list[ArtifactRevision]:
        revisions = []
        for artifact_id in artifact_ids:
            action_result = await ctx.processors.artifact.get_revisions.wait_for_complete(
                GetArtifactRevisionsAction(artifact_id=artifact_id)
            )
            revisions.extend(action_result.revisions)
        return [ArtifactRevision.from_dataclass(r) for r in revisions]

    @classmethod
    def from_dataclass(cls, data: ArtifactData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            # TODO: Fetch status from the actual data source
            # status=ArtifactStatus(data.status),
            status=ArtifactStatus.AVAILABLE,
            description=data.description,
            # TODO: Fill these with actual data
            registry=SourceInfo(name=None, url=None),
            source=SourceInfo(name=None, url=None),
            size=ByteSize(data.size),
            created_at=data.created_at,
            updated_at=data.updated_at,
            version=data.version,
            authorized=data.authorized,
        )


ArtifactEdge = Edge[Artifact]
ArtifactRevisionEdge = Edge[ArtifactRevision]


@strawberry.type
class ArtifactConnection(Connection[Artifact]):
    count: int = 0

    def __init__(self, *args, count: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type
class ArtifactRevisionConnection(Connection[ArtifactRevision]):
    count: int = 0

    def __init__(self, *args, count: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type
class ArtifactImportProgressUpdatedPayload:
    artifact_id: ID
    progress: float
    status: ArtifactStatus


@strawberry.type
class ScanArtifactsPayload:
    artifacts: list[Artifact]


# Mutation Payloads
@strawberry.type
class ImportArtifactsPayload:
    artifacts: ArtifactConnection


@strawberry.type
class UpdateArtifactPayload:
    artifact: Artifact


@strawberry.type
class DeleteArtifactPayload:
    artifact_id: ID


@strawberry.type
class AuthorizeArtifactPayload:
    artifact: Artifact


@strawberry.type
class UnauthorizeArtifactPayload:
    artifact: Artifact


@strawberry.type
class AuthorizeArtifactPayload:
    artifact: Artifact


@strawberry.type
class UnauthorizeArtifactPayload:
    artifact: Artifact


@strawberry.type
class CancelImportArtifactPayload:
    artifact_id: ID


@strawberry.type
class ArtifactStatusChangedPayload:
    artifact: Artifact


async def resolve_artifacts(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactFilter] = None,
    order_by: Optional[list[ArtifactOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactConnection:
    raise NotImplementedError("Artifact retrieval not implemented yet.")


async def resolve_artifact_revisions(
    artifact: Artifact, info: Info[StrawberryGQLContext]
) -> list[ArtifactRevision]:
    raise NotImplementedError("Artifact revision retrieval not implemented yet.")


# Query Fields
@strawberry.field
async def artifacts(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactFilter] = None,
    order_by: Optional[list[ArtifactOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactConnection:
    return await resolve_artifacts(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field
def artifact(id: ID) -> Optional[Artifact]:
    raise NotImplementedError("Artifact retrieval not implemented yet.")


@strawberry.field
def artifact_revision(id: ID) -> Optional[ArtifactRevision]:
    raise NotImplementedError("Artifact revision retrieval not implemented yet.")


@strawberry.mutation
async def scan_artifacts(
    input: ScanArtifactInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactsPayload:
    action_result = await info.context.processors.artifact.scan.wait_for_complete(
        ScanArtifactsAction(
            registry_id=uuid.UUID(input.registry_id),
            storage_id=uuid.UUID(input.storage_id),
            limit=input.limit,
            # TODO: Move this huggingface_registries config if needed
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    artifacts = [Artifact.from_dataclass(item.artifact) for item in action_result.result]
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@strawberry.mutation
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    for artifact in input.artifacts:
        action_result = await info.context.processors.artifact.import_.wait_for_complete(
            ImportArtifactAction(
                artifact_id=uuid.UUID(artifact.artifact_id),
                artifact_version=artifact.revision,
                storage_id=uuid.UUID(input.storage_id),
                bucket_name=input.bucket_name,
            )
        )
        imported_artifacts.append(Artifact.from_dataclass(action_result.result))

    edges = [
        ArtifactEdge(node=artifact, cursor=str(i)) for i, artifact in enumerate(imported_artifacts)
    ]

    artifacts_connection = ArtifactConnection(
        count=len(imported_artifacts),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return ImportArtifactsPayload(artifacts=artifacts_connection)


@strawberry.mutation
def update_artifact(input: UpdateArtifactInput) -> UpdateArtifactPayload:
    raise NotImplementedError("Update artifact functionality is not implemented yet.")


@strawberry.mutation
async def delete_artifact(
    input: DeleteArtifactInput, info: Info[StrawberryGQLContext]
) -> DeleteArtifactPayload:
    action_result = await info.context.processors.artifact.delete.wait_for_complete(
        DeleteArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
        )
    )

    return DeleteArtifactPayload(artifact_id=ID(str(action_result.artifact_id)))


@strawberry.mutation
async def cancel_import_artifact(
    artifact_id: ID, info: Info[StrawberryGQLContext]
) -> CancelImportArtifactPayload:
    # TODO: Cancel actual import bgtask
    action_result = await info.context.processors.artifact.cancel_import.wait_for_complete(
        CancelImportAction(
            artifact_id=uuid.UUID(artifact_id),
        )
    )

    return CancelImportArtifactPayload(artifact_id=ID(str(action_result.artifact_id)))


@strawberry.mutation
async def authorize_artifact(
    input: AuthorizeArtifactInput, info: Info[StrawberryGQLContext]
) -> AuthorizeArtifactPayload:
    action_result = await info.context.processors.artifact.authorize.wait_for_complete(
        AuthorizeArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
        )
    )

    return AuthorizeArtifactPayload(artifact=Artifact.from_dataclass(action_result.result))


@strawberry.mutation
async def unauthorize_artifact(
    input: UnauthorizeArtifactInput, info: Info[StrawberryGQLContext]
) -> UnauthorizeArtifactPayload:
    action_result = await info.context.processors.artifact.unauthorize.wait_for_complete(
        UnauthorizeArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
        )
    )

    return UnauthorizeArtifactPayload(artifact=Artifact.from_dataclass(action_result.result))


@strawberry.mutation
async def authorize_artifact(
    input: AuthorizeArtifactInput, info: Info[StrawberryGQLContext]
) -> AuthorizeArtifactPayload:
    action_result = await info.context.processors.artifact.authorize.wait_for_complete(
        AuthorizeArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
        )
    )

    return AuthorizeArtifactPayload(artifact=Artifact.from_dataclass(action_result.result))


@strawberry.mutation
async def unauthorize_artifact(
    input: UnauthorizeArtifactInput, info: Info[StrawberryGQLContext]
) -> UnauthorizeArtifactPayload:
    action_result = await info.context.processors.artifact.unauthorize.wait_for_complete(
        UnauthorizeArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
        )
    )

    return UnauthorizeArtifactPayload(artifact=Artifact.from_dataclass(action_result.result))


# Subscriptions
@strawberry.subscription
async def artifact_status_changed(
    input: ArtifactStatusChangedInput,
) -> AsyncGenerator[ArtifactStatusChangedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield ArtifactStatusChangedPayload(artifact=Artifact())


@strawberry.subscription
async def artifact_import_progress_updated(
    artifact_id: ID,
) -> AsyncGenerator[ArtifactImportProgressUpdatedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield ArtifactImportProgressUpdatedPayload()
