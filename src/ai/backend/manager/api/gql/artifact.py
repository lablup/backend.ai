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

    def to_repo_filter(self) -> ArtifactFilterOptions:
        repo_filter = ArtifactFilterOptions()

        # Handle artifact type filter
        if self.type:
            # Convert first type from list (assuming single type for now)
            repo_filter.artifact_type = self.type[0] if self.type else None

        # Handle name filter
        if self.name:
            # Use the most specific filter available (starts with preference order)
            if self.name.equals:
                repo_filter.name = self.name.equals
            elif self.name.i_equals:
                repo_filter.name = self.name.i_equals
            elif self.name.contains:
                repo_filter.name = self.name.contains
            elif self.name.i_contains:
                repo_filter.name = self.name.i_contains
            elif self.name.starts_with:
                repo_filter.name = self.name.starts_with
            elif self.name.i_starts_with:
                repo_filter.name = self.name.i_starts_with

        # Note: For now we ignore registry and source filters as they require additional complexity
        # TODO: Add support for registry/source filters when needed

        return repo_filter


@strawberry.input
class ArtifactOrderBy:
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input
class ArtifactRevisionFilter:
    status: Optional[list[ArtifactStatus]] = None
    version: Optional[StringFilter] = None
    artifact_id: Optional[ID] = None

    AND: Optional["ArtifactRevisionFilter"] = None
    OR: Optional["ArtifactRevisionFilter"] = None
    NOT: Optional["ArtifactRevisionFilter"] = None
    DISTINCT: Optional[bool] = None

    def to_repo_filter(self) -> ArtifactRevisionFilterOptions:
        repo_filter = ArtifactRevisionFilterOptions()

        # Handle artifact_id filter
        if self.artifact_id:
            repo_filter.artifact_id = uuid.UUID(self.artifact_id)

        # Handle status filter
        if self.status:
            repo_filter.status = self.status

        # Handle version filter
        if self.version:
            # Use the most specific filter available
            if self.version.equals:
                repo_filter.version = self.version.equals
            elif self.version.i_equals:
                repo_filter.version = self.version.i_equals
            elif self.version.contains:
                repo_filter.version = self.version.contains
            elif self.version.i_contains:
                repo_filter.version = self.version.i_contains
            elif self.version.starts_with:
                repo_filter.version = self.version.starts_with
            elif self.version.i_starts_with:
                repo_filter.version = self.version.i_starts_with

        return repo_filter


@strawberry.input
class ArtifactRevisionOrderBy:
    field: ArtifactRevisionOrderField
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
    async def revisions(
        self,
        info: Info[StrawberryGQLContext],
        filter: Optional[ArtifactRevisionFilter] = None,
        order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ArtifactRevisionConnection:
        return await resolve_artifact_revisions(
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
    def from_dataclass(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            # TODO: Fetch status from the actual data source
            # status=ArtifactStatus(data.status),
            status=ArtifactStatus(ArtifactStatus.AVAILABLE),
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
    repo_filter = None
    if filter:
        repo_filter = filter.to_repo_filter()

    # Convert GraphQL ordering to repository ordering
    repo_ordering = _convert_gql_ordering_to_repo_ordering(order_by)

    # Set up pagination options
    pagination_options = build_pagination_options(
        before=before, after=after, first=first, last=last, limit=limit, offset=offset
    )

    # Get artifacts using list action
    action_result = await info.context.processors.artifact.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=pagination_options, ordering=repo_ordering, filters=repo_filter
        )
    )

    # Build GraphQL connection response
    return _build_artifact_connection(
        artifacts=action_result.data,
        total_count=action_result.total_count,
        pagination_options=pagination_options,
    )


def _convert_gql_ordering_to_repo_ordering(
    order_by: Optional[list[ArtifactOrderBy]],
) -> ArtifactOrderingOptions:
    """Convert GraphQL ordering to repository ordering options"""
    if not order_by:
        return ArtifactOrderingOptions()  # Uses default ordering

    repo_order_by = []
    for order in order_by:
        desc = order.direction == OrderDirection.DESC
        repo_order_by.append((order.field, desc))

    return ArtifactOrderingOptions(order_by=repo_order_by)


def _convert_gql_ordering_to_repo_ordering_revision(
    order_by: Optional[list[ArtifactRevisionOrderBy]],
) -> ArtifactRevisionOrderingOptions:
    """Convert GraphQL ordering to repository ordering options for revisions"""
    if not order_by:
        return ArtifactRevisionOrderingOptions()  # Uses default ordering

    repo_order_by = []
    for order in order_by:
        desc = order.direction == OrderDirection.DESC
        repo_order_by.append((order.field, desc))

    return ArtifactRevisionOrderingOptions(order_by=repo_order_by)


def _build_artifact_connection(
    artifacts: list[ArtifactData],
    total_count: int,
    pagination_options: PaginationOptions,
) -> ArtifactConnection:
    """Build GraphQL connection from artifacts data"""
    edges = []
    for i, artifact_data in enumerate(artifacts):
        artifact = Artifact.from_dataclass(artifact_data)
        cursor = str(artifact_data.id)  # Use artifact ID as cursor
        edges.append(ArtifactEdge(node=artifact, cursor=cursor))

    # Calculate pagination info
    has_next_page = False
    has_previous_page = False

    if pagination_options.offset:
        # Offset-based pagination
        offset = pagination_options.offset.offset or 0

        has_previous_page = offset > 0
        has_next_page = (offset + len(artifacts)) < total_count

    elif pagination_options.forward:
        # Forward pagination (after/first)
        first = pagination_options.forward.first
        if first is not None:
            # If we got exactly the requested number and there might be more
            has_next_page = len(artifacts) == first
        else:
            # If no first specified, check if we have all items
            has_next_page = len(artifacts) < total_count
        has_previous_page = pagination_options.forward.after is not None

    elif pagination_options.backward:
        # Backward pagination (before/last)
        last = pagination_options.backward.last
        if last is not None:
            # If we got exactly the requested number, there might be more before
            has_previous_page = len(artifacts) == last
        else:
            # If no last specified, assume there could be previous items
            has_previous_page = True
        has_next_page = pagination_options.backward.before is not None

    else:
        # Default case - assume we have all items if no pagination specified
        has_next_page = len(artifacts) < total_count
        has_previous_page = False

    page_info = strawberry.relay.PageInfo(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactConnection(
        count=total_count,
        edges=edges,
        page_info=page_info,
    )


def _build_artifact_revision_connection(
    artifact_revisions: list[ArtifactRevisionData],
    total_count: int,
    pagination_options: PaginationOptions,
) -> ArtifactRevisionConnection:
    """Build GraphQL connection from artifact revision data"""
    edges = []
    for i, revision_data in enumerate(artifact_revisions):
        revision = ArtifactRevision.from_dataclass(revision_data)
        cursor = str(revision_data.id)  # Use revision ID as cursor
        edges.append(ArtifactRevisionEdge(node=revision, cursor=cursor))

    # Calculate pagination info
    has_next_page = False
    has_previous_page = False

    if pagination_options.offset:
        # Offset-based pagination
        offset = pagination_options.offset.offset or 0

        has_previous_page = offset > 0
        has_next_page = (offset + len(artifact_revisions)) < total_count

    elif pagination_options.forward:
        # Forward pagination (after/first)
        first = pagination_options.forward.first
        if first is not None:
            # If we got exactly the requested number and there might be more
            has_next_page = len(artifact_revisions) == first
        else:
            # If no first specified, check if we have all items
            has_next_page = len(artifact_revisions) < total_count
        has_previous_page = pagination_options.forward.after is not None

    elif pagination_options.backward:
        # Backward pagination (before/last)
        last = pagination_options.backward.last
        if last is not None:
            # If we got exactly the requested number, there might be more before
            has_previous_page = len(artifact_revisions) == last
        else:
            # If no last specified, assume there could be previous items
            has_previous_page = True
        has_next_page = pagination_options.backward.before is not None

    else:
        # Default case - assume we have all items if no pagination specified
        has_next_page = len(artifact_revisions) < total_count
        has_previous_page = False

    page_info = strawberry.relay.PageInfo(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ArtifactRevisionConnection(
        count=total_count,
        edges=edges,
        page_info=page_info,
    )


async def resolve_artifact_revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactRevisionFilter] = None,
    order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactRevisionConnection:
    repo_filter = None
    if filter:
        repo_filter = filter.to_repo_filter()

    # Convert GraphQL ordering to repository ordering
    repo_ordering = _convert_gql_ordering_to_repo_ordering_revision(order_by)

    # Set up pagination options
    pagination_options = build_pagination_options(
        before=before, after=after, first=first, last=last, limit=limit, offset=offset
    )

    # Get artifact revisions using list action
    action_result = await info.context.processors.artifact_revision.list_.wait_for_complete(
        ListArtifactRevisionsAction(
            pagination=pagination_options,
            ordering=repo_ordering,
            filters=repo_filter,
        )
    )

    # Build GraphQL connection response
    return _build_artifact_revision_connection(
        artifact_revisions=action_result.data,
        total_count=action_result.total_count,
        pagination_options=pagination_options,
    )


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
async def artifact(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Artifact]:
    action_result = await info.context.processors.artifact.get.wait_for_complete(
        GetArtifactAction(
            artifact_id=uuid.UUID(id),
        )
    )

    return Artifact.from_dataclass(action_result.result)


@strawberry.field
async def artifact_revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactRevisionFilter] = None,
    order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ArtifactRevisionConnection:
    return await resolve_artifact_revisions(
        info,
        filter,
        order_by,
        before,
        after,
        first,
        last,
        limit,
        offset,
    )


@strawberry.field
async def artifact_revision(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ArtifactRevision]:
    action_result = await info.context.processors.artifact_revision.get.wait_for_complete(
        GetArtifactRevisionAction(
            revision_id=uuid.UUID(id),
        )
    )

    return ArtifactRevision.from_dataclass(action_result.revision)


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
