from __future__ import annotations

import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Self, Sequence

import strawberry
from aiotools import apartial
from strawberry import ID, UNSET, Info
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.api.gql.base import (
    ByteSize,
    OrderDirection,
    StringFilter,
    build_pagination_options,
)
from ai.backend.manager.api.gql.huggingface_registry import HuggingFaceRegistry
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactOrderField,
    ArtifactRevisionData,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.repositories.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    ArtifactRevisionFilterOptions,
    ArtifactRevisionOrderingOptions,
    ArtifactStatusFilter,
    ArtifactStatusFilterType,
)
from ai.backend.manager.repositories.types import PaginationOptions
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.get_revisions import GetArtifactRevisionsAction
from ai.backend.manager.services.artifact.actions.list import ListArtifactsAction
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact_revision.actions.delete import (
    DeleteArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.list import ListArtifactRevisionsAction
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.types import TriState


@strawberry.input(description="Added in 25.13.0")
class ArtifactFilter:
    type: Optional[list[ArtifactType]] = None
    name: Optional[StringFilter] = None
    registry: Optional[StringFilter] = None
    source: Optional[StringFilter] = None

    AND: Optional[list["ArtifactFilter"]] = None
    OR: Optional[list["ArtifactFilter"]] = None
    NOT: Optional[list["ArtifactFilter"]] = None
    DISTINCT: Optional[bool] = None

    def to_repo_filter(self) -> ArtifactFilterOptions:
        repo_filter = ArtifactFilterOptions()

        # Handle basic filters
        if self.type:
            repo_filter.artifact_type = self.type[0] if self.type else None

        repo_filter.name_filter = self.name
        repo_filter.registry_filter = self.registry
        repo_filter.source_filter = self.source

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.13.0")
class ArtifactOrderBy:
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input(description="Added in 25.13.0")
class ArtifactRevisionStatusFilter:
    in_: Optional[list[ArtifactStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ArtifactStatus] = None


@strawberry.input(description="Added in 25.13.0")
class ArtifactRevisionFilter:
    status: Optional[ArtifactRevisionStatusFilter] = None
    version: Optional[StringFilter] = None
    artifact_id: Optional[ID] = None

    AND: Optional[list["ArtifactRevisionFilter"]] = None
    OR: Optional[list["ArtifactRevisionFilter"]] = None
    NOT: Optional[list["ArtifactRevisionFilter"]] = None
    DISTINCT: Optional[bool] = None

    def to_repo_filter(self) -> ArtifactRevisionFilterOptions:
        repo_filter = ArtifactRevisionFilterOptions()

        # Handle basic filters
        if self.artifact_id:
            repo_filter.artifact_id = uuid.UUID(self.artifact_id)

        # Handle status filter using ArtifactRevisionStatusFilter
        if self.status:
            if self.status.in_:
                repo_filter.status_filter = ArtifactStatusFilter(
                    type=ArtifactStatusFilterType.IN, values=self.status.in_
                )
            elif self.status.equals:
                repo_filter.status_filter = ArtifactStatusFilter(
                    type=ArtifactStatusFilterType.EQUALS, values=[self.status.equals]
                )

        # Pass StringFilter directly for processing in repository
        repo_filter.version_filter = self.version

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.13.0")
class ArtifactRevisionOrderBy:
    field: ArtifactRevisionOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input(description="Added in 25.13.0")
class ScanArtifactsInput:
    registry_id: ID
    storage_namespace_id: ID
    limit: int
    search: Optional[str] = None


@strawberry.input(description="Added in 25.13.0")
class ImportArtifactsInput:
    artifact_revision_ids: list[ID]
    storage_namespace_id: ID


@strawberry.input(description="Added in 25.13.0")
class UpdateArtifactInput:
    artifact_id: ID
    readonly: Optional[bool] = UNSET


@strawberry.input(description="Added in 25.13.0")
class CancelArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.13.0")
class DeleteArtifactRevisionTarget:
    artifact_revision_id: ID
    storage_namespace_id: ID


@strawberry.input(description="Added in 25.13.0")
class DeleteArtifactRevisionsInput:
    targets: list[DeleteArtifactRevisionTarget]


@strawberry.input(description="Added in 25.13.0")
class ApproveArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.13.0")
class RejectArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.13.0")
class ArtifactStatusChangedInput:
    artifact_revision_ids: list[ID]


# Object Types
@strawberry.type(description="Added in 25.13.0")
class SourceInfo:
    name: Optional[str]
    url: Optional[str]


@strawberry.type(description="Added in 25.13.0")
class Artifact(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    readonly: bool

    @classmethod
    def from_dataclass(cls, data: ArtifactData, registry_url: str, source_url: str) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry=SourceInfo(name=data.registry_type.value, url=registry_url),
            source=SourceInfo(name=data.source_registry_type.value, url=source_url),
            readonly=data.readonly,
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
        if filter is None:
            filter = ArtifactRevisionFilter(artifact_id=ID(self.id))
        else:
            filter.artifact_id = ID(self.id)

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
    async def updated_at(self, info: Info[StrawberryGQLContext]) -> Optional[datetime]:
        action_result = await info.context.processors.artifact.get_revisions.wait_for_complete(
            GetArtifactRevisionsAction(uuid.UUID(self.id))
        )

        updated_at_list = [
            r.updated_at for r in action_result.revisions if r.updated_at is not None
        ]
        return max(updated_at_list) if updated_at_list else None


@strawberry.type(description="Added in 25.13.0")
class ArtifactRevision(Node):
    id: NodeID[str]
    status: ArtifactStatus
    version: str
    readme: Optional[str]
    size: Optional[ByteSize]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_dataclass(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            status=ArtifactStatus(data.status),
            readme=data.readme,
            version=data.version,
            size=ByteSize(data.size) if data.size is not None else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
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


@strawberry.type(description="Added in 25.13.0")
class ArtifactConnection(Connection[Artifact]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(description="Added in 25.13.0")
class ArtifactRevisionConnection(Connection[ArtifactRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(description="Added in 25.13.0")
class ArtifactImportProgressUpdatedPayload:
    artifact_id: ID
    progress: float
    status: ArtifactStatus


@strawberry.type(description="Added in 25.13.0")
class ScanArtifactsPayload:
    artifacts: list[Artifact]


# Mutation Payloads
@strawberry.type(description="Added in 25.13.0")
class ImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection
    task_ids: list[uuid.UUID]


@strawberry.type(description="Added in 25.13.0")
class UpdateArtifactPayload:
    artifact: Artifact


@strawberry.type(description="Added in 25.13.0")
class DeleteArtifactRevisionsPayload:
    artifact_revision_ids: list[ID]


@strawberry.type(description="Added in 25.13.0")
class ApproveArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(description="Added in 25.13.0")
class RejectArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type
class CancelImportArtifactPayload:
    artifact_revision_id: ID


@strawberry.type(description="Added in 25.13.0")
class ArtifactStatusChangedPayload:
    artifact_revision: ArtifactRevision


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
    repo_ordering = _convert_gql_artifact_ordering_to_repo_ordering(order_by)

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

    registry_loader = DataLoader(
        apartial(HuggingFaceRegistry.load_by_id, info.context),
    )

    # Build GraphQL connection response
    return await _build_artifact_connection(
        registry_loader,
        artifacts=action_result.data,
        total_count=action_result.total_count,
        pagination_options=pagination_options,
    )


def _convert_gql_artifact_ordering_to_repo_ordering(
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


def _convert_gql_artifact_revision_ordering_to_repo_ordering(
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


async def _build_artifact_connection(
    registry_loader: DataLoader,
    artifacts: list[ArtifactData],
    total_count: int,
    pagination_options: PaginationOptions,
) -> ArtifactConnection:
    """Build GraphQL connection from artifacts data"""
    edges = []

    for i, artifact_data in enumerate(artifacts):
        registry_data = await registry_loader.load(artifact_data.registry_id)
        source_registry_data = await registry_loader.load(artifact_data.source_registry_id)
        artifact = Artifact.from_dataclass(
            artifact_data, registry_url=registry_data.url, source_url=source_registry_data.url
        )
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
    repo_ordering = _convert_gql_artifact_revision_ordering_to_repo_ordering(order_by)

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
@strawberry.field(description="Added in 25.13.0")
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
    artifacts = await resolve_artifacts(
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

    return artifacts


@strawberry.field(description="Added in 25.13.0")
async def artifact(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Artifact]:
    action_result = await info.context.processors.artifact.get.wait_for_complete(
        GetArtifactAction(
            artifact_id=uuid.UUID(id),
        )
    )

    registry_loader = DataLoader(
        apartial(HuggingFaceRegistry.load_by_id, info.context),
    )

    registry_data = await registry_loader.load(action_result.result.registry_id)
    source_registry_data = await registry_loader.load(action_result.result.source_registry_id)

    return Artifact.from_dataclass(
        action_result.result, registry_data.url, source_registry_data.url
    )


@strawberry.field(description="Added in 25.13.0")
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


@strawberry.field(description="Added in 25.13.0")
async def artifact_revision(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ArtifactRevision]:
    action_result = await info.context.processors.artifact_revision.get.wait_for_complete(
        GetArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(id),
        )
    )

    return ArtifactRevision.from_dataclass(action_result.revision)


@strawberry.mutation(description="Added in 25.13.0")
async def scan_artifacts(
    input: ScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactsPayload:
    action_result = await info.context.processors.artifact.scan.wait_for_complete(
        ScanArtifactsAction(
            registry_id=uuid.UUID(input.registry_id),
            storage_namespace_id=uuid.UUID(input.storage_namespace_id),
            limit=input.limit,
            # TODO: Move this huggingface_registries config if needed
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    registry_loader = DataLoader(
        apartial(HuggingFaceRegistry.load_by_id, info.context),
    )
    artifacts = []
    for item in action_result.result:
        registry_data = await registry_loader.load(item.artifact.registry_id)
        source_registry_data = await registry_loader.load(item.artifact.source_registry_id)
        artifacts.append(
            Artifact.from_dataclass(item.artifact, registry_data.url, source_registry_data.url)
        )
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@strawberry.mutation(description="Added in 25.13.0")
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    task_ids = []
    for revision_id in input.artifact_revision_ids:
        action_result = await info.context.processors.artifact_revision.import_.wait_for_complete(
            ImportArtifactRevisionAction(
                artifact_revision_id=uuid.UUID(revision_id),
                storage_namespace_id=uuid.UUID(input.storage_namespace_id),
            )
        )
        imported_artifacts.append(ArtifactRevision.from_dataclass(action_result.result))
        task_ids.append(action_result.task_id)

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=str(i))
        for i, artifact in enumerate(imported_artifacts)
    ]

    artifacts_connection = ArtifactRevisionConnection(
        count=len(imported_artifacts),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return ImportArtifactsPayload(artifact_revisions=artifacts_connection, task_ids=task_ids)


@strawberry.mutation(description="Added in 25.13.0")
async def update_artifact(
    input: UpdateArtifactInput, info: Info[StrawberryGQLContext]
) -> UpdateArtifactPayload:
    action_result = await info.context.processors.artifact.update.wait_for_complete(
        UpdateArtifactAction(
            artifact_id=uuid.UUID(input.artifact_id),
            modifier=ArtifactModifier(readonly=TriState.from_graphql(input.readonly)),
        )
    )

    artifact = action_result.result
    registry_loader = DataLoader(
        apartial(HuggingFaceRegistry.load_by_id, info.context),
    )

    registry_data = await registry_loader.load(artifact.registry_id)
    source_registry_data = await registry_loader.load(artifact.source_registry_id)

    return UpdateArtifactPayload(
        artifact=Artifact.from_dataclass(
            artifact, registry_url=registry_data.url, source_url=source_registry_data.url
        )
    )


@strawberry.mutation(description="Added in 25.13.0")
async def delete_artifact_revisions(
    input: DeleteArtifactRevisionsInput, info: Info[StrawberryGQLContext]
) -> DeleteArtifactRevisionsPayload:
    artifact_revision_ids = []
    for target in input.targets:
        action_result = await info.context.processors.artifact_revision.delete.wait_for_complete(
            DeleteArtifactRevisionAction(
                artifact_revision_id=uuid.UUID(target.artifact_revision_id),
                storage_namespace_id=uuid.UUID(target.storage_namespace_id),
            )
        )
        artifact_revision_ids.append(ID(str(action_result.artifact_revision_id)))

    return DeleteArtifactRevisionsPayload(artifact_revision_ids=artifact_revision_ids)


@strawberry.mutation(description="Added in 25.13.0")
async def cancel_import_artifact(
    input: CancelArtifactInput, info: Info[StrawberryGQLContext]
) -> CancelImportArtifactPayload:
    # TODO: Cancel actual import bgtask
    action_result = await info.context.processors.artifact_revision.cancel_import.wait_for_complete(
        CancelImportAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )
    return CancelImportArtifactPayload(
        artifact_revision_id=ID(str(action_result.artifact_revision_id))
    )


# TODO: Make this available when only having super-admin privileges
@strawberry.mutation(description="Added in 25.13.0")
async def approve_artifact_revision(
    input: ApproveArtifactInput, info: Info[StrawberryGQLContext]
) -> ApproveArtifactPayload:
    action_result = await info.context.processors.artifact_revision.approve.wait_for_complete(
        ApproveArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )

    return ApproveArtifactPayload(
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


@strawberry.mutation(description="Added in 25.13.0")
async def reject_artifact_revision(
    input: RejectArtifactInput, info: Info[StrawberryGQLContext]
) -> RejectArtifactPayload:
    action_result = await info.context.processors.artifact_revision.reject.wait_for_complete(
        RejectArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(input.artifact_revision_id),
        )
    )

    return RejectArtifactPayload(
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


# Subscriptions
@strawberry.subscription(description="Added in 25.13.0")
async def artifact_status_changed(
    input: ArtifactStatusChangedInput,
) -> AsyncGenerator[ArtifactStatusChangedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield ArtifactStatusChangedPayload(artifact=Artifact())


@strawberry.subscription(description="Added in 25.13.0")
async def artifact_import_progress_updated(
    artifact_revision_id: ID,
) -> AsyncGenerator[ArtifactImportProgressUpdatedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield ArtifactImportProgressUpdatedPayload()
