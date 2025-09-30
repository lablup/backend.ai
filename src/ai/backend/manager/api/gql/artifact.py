from __future__ import annotations

import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Self

import strawberry
from aiotools import apartial
from strawberry import ID, UNSET, Info
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.common.data.storage.registries.types import ModelTarget as ModelTargetData
from ai.backend.manager.api.gql.base import (
    ByteSize,
    IntFilter,
    OrderDirection,
    StringFilter,
    build_pagination_options,
    to_global_id,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactOrderField,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact.types import DelegateeTarget as DelegateeTargetData
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.errors.api import NotImplementedAPI
from ai.backend.manager.errors.artifact import ArtifactScanLimitExceededError
from ai.backend.manager.repositories.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    ArtifactRevisionFilterOptions,
    ArtifactRevisionOrderingOptions,
    ArtifactStatusFilter,
    ArtifactStatusFilterType,
)
from ai.backend.manager.services.artifact.actions.delegate_scan import DelegateScanArtifactsAction
from ai.backend.manager.services.artifact.actions.delete_multi import DeleteArtifactsAction
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.list import ListArtifactsAction
from ai.backend.manager.services.artifact.actions.restore_multi import RestoreArtifactsAction
from ai.backend.manager.services.artifact.actions.retrieve_model_multi import RetrieveModelsAction
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.update import UpdateArtifactAction
from ai.backend.manager.services.artifact_revision.actions.approve import (
    ApproveArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact_revision.actions.cleanup import (
    CleanupArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact_revision.actions.import_revision import (
    ImportArtifactRevisionAction,
)
from ai.backend.manager.services.artifact_revision.actions.list import ListArtifactRevisionsAction
from ai.backend.manager.services.artifact_revision.actions.reject import (
    RejectArtifactRevisionAction,
)
from ai.backend.manager.types import PaginationOptions, TriState

from .artifact_registry_meta import ArtifactRegistryMeta


@strawberry.input(description="Added in 25.14.0")
class ArtifactFilter:
    type: Optional[list[ArtifactType]] = None
    name: Optional[StringFilter] = None
    registry: Optional[StringFilter] = None
    source: Optional[StringFilter] = None
    availability: Optional[list[ArtifactAvailability]] = None

    AND: Optional[list["ArtifactFilter"]] = None
    OR: Optional[list["ArtifactFilter"]] = None
    NOT: Optional[list["ArtifactFilter"]] = None

    def to_repo_filter(self) -> ArtifactFilterOptions:
        repo_filter = ArtifactFilterOptions()

        # Handle basic filters
        repo_filter.artifact_type = self.type
        repo_filter.name_filter = self.name
        repo_filter.registry_filter = self.registry
        repo_filter.source_filter = self.source
        repo_filter.availability = self.availability

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.14.0")
class ArtifactOrderBy:
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input(description="Added in 25.14.0")
class ArtifactRevisionStatusFilter:
    in_: Optional[list[ArtifactStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ArtifactStatus] = None


@strawberry.input(description="Added in 25.14.0")
class ArtifactRevisionFilter:
    status: Optional[ArtifactRevisionStatusFilter] = None
    version: Optional[StringFilter] = None
    artifact_id: Optional[ID] = None
    size: Optional[IntFilter] = None

    AND: Optional[list["ArtifactRevisionFilter"]] = None
    OR: Optional[list["ArtifactRevisionFilter"]] = None
    NOT: Optional[list["ArtifactRevisionFilter"]] = None

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

        # Handle size filter
        repo_filter.size_filter = self.size

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(description="Added in 25.14.0")
class ArtifactRevisionOrderBy:
    field: ArtifactRevisionOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input(description="Added in 25.14.0")
class ScanArtifactsInput:
    registry_id: Optional[ID] = None
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: Optional[ArtifactType] = None
    search: Optional[str] = None


@strawberry.input(description="Added in 25.14.0")
class ImportArtifactsInput:
    artifact_revision_ids: list[ID]


@strawberry.input(description="Added in 25.15.0")
class DelegateeTarget:
    delegatee_reservoir_id: ID
    target_registry_id: ID

    def to_dataclass(self) -> DelegateeTargetData:
        return DelegateeTargetData(
            delegatee_reservoir_id=uuid.UUID(self.delegatee_reservoir_id),
            target_registry_id=uuid.UUID(self.target_registry_id),
        )


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated scanning of artifacts from a delegatee reservoir registry's remote registry.
""")
)
class DelegateScanArtifactsInput:
    delegator_reservoir_id: Optional[ID] = strawberry.field(
        default=None, description="ID of the reservoir registry to delegate the scan request to"
    )
    delegatee_target: Optional[DelegateeTarget] = strawberry.field(
        default=None,
        description="Target delegatee reservoir registry and its remote registry to scan",
    )
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: Optional[ArtifactType] = strawberry.field(
        default=None, description="Filter artifacts by type (e.g., model, image, package)"
    )
    search: Optional[str] = strawberry.field(
        default=None, description="Search term to filter artifacts by name or description"
    )


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated import of artifact revisions from a reservoir registry's remote registry.
    Used to specify which artifact revisions should be imported from the remote registry source
    into the local reservoir registry storage.
""")
)
class DelegateImportArtifactsInput:
    artifact_revision_ids: list[ID] = strawberry.field(
        description="List of artifact revision IDs of delegatee artifact registry"
    )


@strawberry.input(description="Added in 25.14.0")
class UpdateArtifactInput:
    artifact_id: ID
    readonly: Optional[bool] = UNSET


@strawberry.input(description="Added in 25.14.0")
class CancelArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.14.0")
class CleanupArtifactRevisionsInput:
    artifact_revision_ids: list[ID]


@strawberry.input(description="Added in 25.15.0")
class DeleteArtifactsInput:
    artifact_ids: list[ID]


@strawberry.input(description="Added in 25.15.0")
class RestoreArtifactsInput:
    artifact_ids: list[ID]


@strawberry.input(description="Added in 25.14.0")
class ApproveArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.14.0")
class RejectArtifactInput:
    artifact_revision_id: ID


@strawberry.input(description="Added in 25.14.0")
class ArtifactStatusChangedInput:
    artifact_revision_ids: list[ID]


@strawberry.input(description="Added in 25.14.0")
class ModelTarget:
    model_id: str
    revision: Optional[str] = None

    def to_dataclass(self) -> ModelTargetData:
        return ModelTargetData(model_id=self.model_id, revision=self.revision)


@strawberry.input(description="Added in 25.14.0")
class ScanArtifactModelsInput:
    models: list[ModelTarget]
    registry_id: Optional[uuid.UUID] = None


# Object Types
@strawberry.type(description="Added in 25.14.0")
class SourceInfo:
    name: Optional[str]
    url: Optional[str]


@strawberry.type(description="Added in 25.14.0")
class Artifact(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    readonly: bool
    scanned_at: datetime
    updated_at: datetime
    availability: ArtifactAvailability

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
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            availability=data.availability,
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


@strawberry.type(description="Added in 25.14.0")
class ArtifactRevision(Node):
    id: NodeID[str]
    status: ArtifactStatus
    remote_status: Optional[ArtifactRemoteStatus] = strawberry.field(description="Added in 25.15.0")
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
            remote_status=ArtifactRemoteStatus(data.remote_status) if data.remote_status else None,
            readme=data.readme,
            version=data.version,
            size=ByteSize(data.size) if data.size is not None else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @strawberry.field
    async def artifact(self, info: Info[StrawberryGQLContext]) -> Artifact:
        revision_action_result = (
            await info.context.processors.artifact_revision.get.wait_for_complete(
                GetArtifactRevisionAction(artifact_revision_id=uuid.UUID(self.id))
            )
        )

        artifact_id = revision_action_result.revision.artifact_id

        artifact_action_result = await info.context.processors.artifact.get.wait_for_complete(
            GetArtifactAction(artifact_id=artifact_id)
        )

        registry_meta_loader = DataLoader(
            apartial(ArtifactRegistryMeta.load_by_id, info.context),
        )

        registry_data = await registry_meta_loader.load(artifact_action_result.result.registry_id)
        source_registry_data = await registry_meta_loader.load(
            artifact_action_result.result.source_registry_id
        )

        return Artifact.from_dataclass(
            artifact_action_result.result, registry_data.url, source_registry_data.url
        )


ArtifactEdge = Edge[Artifact]
ArtifactRevisionEdge = Edge[ArtifactRevision]


@strawberry.type(description="Added in 25.14.0")
class ArtifactConnection(Connection[Artifact]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(description="Added in 25.14.0")
class ArtifactRevisionConnection(Connection[ArtifactRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(description="Added in 25.14.0")
class ArtifactImportProgressUpdatedPayload:
    artifact_id: ID
    progress: float
    status: ArtifactStatus


@strawberry.type(description="Added in 25.14.0")
class ScanArtifactsPayload:
    artifacts: list[Artifact]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for delegated artifact scanning operation.
    Contains the list of artifacts discovered during the scan of a reservoir registry's remote registry.
    These artifacts are now available for import or direct use.
""")
)
class DelegateScanArtifactsPayload:
    artifacts: list[Artifact] = strawberry.field(
        description="List of artifacts discovered during the delegated scan from the reservoir registry's remote registry"
    )


@strawberry.type(description="Added in 25.14.0")
class ArtifactRevisionImportTask:
    task_id: ID
    artifact_revision: ArtifactRevision


# Mutation Payloads
@strawberry.type(description="Added in 25.14.0")
class ImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection
    tasks: list[ArtifactRevisionImportTask]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for delegated artifact import operation.
    Contains the imported artifact revisions and associated background tasks.
    The tasks can be monitored to track the progress of the import operation.
""")
)
class DelegateImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection = strawberry.field(
        description="Connection of artifact revisions that were imported from the reservoir registry's remote registry"
    )
    tasks: list[ArtifactRevisionImportTask] = strawberry.field(
        description="List of background tasks created for importing the artifact revisions"
    )


@strawberry.type(description="Added in 25.14.0")
class UpdateArtifactPayload:
    artifact: Artifact


@strawberry.type(description="Added in 25.14.0")
class CleanupArtifactRevisionsPayload:
    artifact_revisions: ArtifactRevisionConnection


@strawberry.type(description="Added in 25.14.0")
class ApproveArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(description="Added in 25.14.0")
class RejectArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type
class CancelImportArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(description="Added in 25.14.0")
class ArtifactStatusChangedPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(description="Added in 25.14.0")
class ScanArtifactModelsPayload:
    artifact_revision: ArtifactRevisionConnection


@strawberry.type(description="Added in 25.15.0")
class DeleteArtifactsPayload:
    artifacts: list[Artifact]


@strawberry.type(description="Added in 25.15.0")
class RestoreArtifactsPayload:
    artifacts: list[Artifact]


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

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    # Build GraphQL connection response
    return await _build_artifact_connection(
        registry_meta_loader,
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
    registry_meta_loader: DataLoader,
    artifacts: list[ArtifactData],
    total_count: int,
    pagination_options: PaginationOptions,
) -> ArtifactConnection:
    """Build GraphQL connection from artifacts data"""
    edges = []

    for artifact_data in artifacts:
        registry_meta = await registry_meta_loader.load(artifact_data.registry_id)
        source_registry_meta = await registry_meta_loader.load(artifact_data.source_registry_id)
        artifact = Artifact.from_dataclass(
            artifact_data, registry_url=registry_meta.url, source_url=source_registry_meta.url
        )
        cursor = to_global_id(Artifact, artifact_data.id)
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
    for revision_data in artifact_revisions:
        revision = ArtifactRevision.from_dataclass(revision_data)
        cursor = to_global_id(ArtifactRevision, revision_data.id)
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
    action_result = await info.context.processors.artifact_revision.list_revision.wait_for_complete(
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
@strawberry.field(description="Added in 25.14.0")
async def artifacts(
    info: Info[StrawberryGQLContext],
    filter: Optional[ArtifactFilter] = ArtifactFilter(availability=[ArtifactAvailability.ALIVE]),
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


@strawberry.field(description="Added in 25.14.0")
async def artifact(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Artifact]:
    action_result = await info.context.processors.artifact.get.wait_for_complete(
        GetArtifactAction(
            artifact_id=uuid.UUID(id),
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    registry_data = await registry_meta_loader.load(action_result.result.registry_id)
    source_registry_data = await registry_meta_loader.load(action_result.result.source_registry_id)

    return Artifact.from_dataclass(
        action_result.result, registry_data.url, source_registry_data.url
    )


@strawberry.field(description="Added in 25.14.0")
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


@strawberry.field(description="Added in 25.14.0")
async def artifact_revision(id: ID, info: Info[StrawberryGQLContext]) -> Optional[ArtifactRevision]:
    action_result = await info.context.processors.artifact_revision.get.wait_for_complete(
        GetArtifactRevisionAction(
            artifact_revision_id=uuid.UUID(id),
        )
    )

    return ArtifactRevision.from_dataclass(action_result.revision)


@strawberry.mutation(description="Added in 25.14.0")
async def scan_artifacts(
    input: ScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    action_result = await info.context.processors.artifact.scan.wait_for_complete(
        ScanArtifactsAction(
            artifact_type=input.artifact_type,
            registry_id=uuid.UUID(input.registry_id) if input.registry_id else None,
            limit=input.limit,
            # TODO: Move this huggingface_registries config if needed
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    artifacts = []
    for item in action_result.result:
        registry_data = await registry_meta_loader.load(item.registry_id)
        source_registry_data = await registry_meta_loader.load(item.source_registry_id)
        artifacts.append(Artifact.from_dataclass(item, registry_data.url, source_registry_data.url))
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@strawberry.mutation(description="Added in 25.14.0")
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    tasks = []
    for revision_id in input.artifact_revision_ids:
        action_result = (
            await info.context.processors.artifact_revision.import_revision.wait_for_complete(
                ImportArtifactRevisionAction(
                    artifact_revision_id=uuid.UUID(revision_id),
                )
            )
        )
        artifact_revision = ArtifactRevision.from_dataclass(action_result.result)
        imported_artifacts.append(artifact_revision)
        tasks.append(
            ArtifactRevisionImportTask(
                task_id=ID(str(action_result.task_id)),
                artifact_revision=artifact_revision,
            )
        )

    edges = [
        ArtifactRevisionEdge(node=artifact, cursor=to_global_id(ArtifactRevisionEdge, artifact.id))
        for artifact in imported_artifacts
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

    return ImportArtifactsPayload(artifact_revisions=artifacts_connection, tasks=tasks)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Triggers artifact scanning on a remote reservoir registry.

    This mutation instructs a reservoir-type registry to initiate a scan of artifacts
    from its associated remote reservoir registry source. The scan process will discover and
    catalog artifacts available in the remote reservoir, making them accessible
    through the local reservoir registry.

    Requirements:
    - The delegator registry must be of type 'reservoir'
    - The delegator reservoir registry must have a valid remote registry configuration
""")
)
async def delegate_scan_artifacts(
    input: DelegateScanArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateScanArtifactsPayload:
    if input.limit > ARTIFACT_MAX_SCAN_LIMIT:
        raise ArtifactScanLimitExceededError(f"Limit cannot exceed {ARTIFACT_MAX_SCAN_LIMIT}")

    delegator_reservoir_id = (
        uuid.UUID(input.delegator_reservoir_id) if input.delegator_reservoir_id else None
    )

    action_result = await info.context.processors.artifact.delegate_scan.wait_for_complete(
        DelegateScanArtifactsAction(
            delegator_reservoir_id=delegator_reservoir_id,
            delegatee_target=input.delegatee_target.to_dataclass()
            if input.delegatee_target
            else None,
            artifact_type=input.artifact_type,
            limit=input.limit,
            order=ModelSortKey.DOWNLOADS,
            search=input.search,
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    artifacts = []
    for item in action_result.result:
        registry_data = await registry_meta_loader.load(item.registry_id)
        source_registry_data = await registry_meta_loader.load(item.source_registry_id)
        artifacts.append(Artifact.from_dataclass(item, registry_data.url, source_registry_data.url))
    return DelegateScanArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(
    description=dedent_strip("""
    Added in 25.15.0.

    Trigger import of artifact revisions from a remote reservoir registry.

    This mutation instructs a reservoir-type registry to import specific artifact revisions
    that were previously discovered during a scan from its remote registry.
    Note that this operation does not import the artifacts directly into the local registry, but only into the delegator reservoir's storage.

    Requirements:
    - The delegator registry must be of type 'reservoir'
    - The delegator registry must have a valid remote registry configuration
""")
)
async def delegate_import_artifacts(
    input: DelegateImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> DelegateImportArtifactsPayload:
    raise NotImplementedAPI("This mutation is not implemented yet.")


@strawberry.mutation(description="Added in 25.14.0")
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
    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    registry_data = await registry_meta_loader.load(artifact.registry_id)
    source_registry_data = await registry_meta_loader.load(artifact.source_registry_id)

    return UpdateArtifactPayload(
        artifact=Artifact.from_dataclass(
            artifact, registry_url=registry_data.url, source_url=source_registry_data.url
        )
    )


@strawberry.mutation(description="Added in 25.14.0")
async def cleanup_artifact_revisions(
    input: CleanupArtifactRevisionsInput, info: Info[StrawberryGQLContext]
) -> CleanupArtifactRevisionsPayload:
    cleaned_artifact_revisions: list[ArtifactRevision] = []
    # TODO: Refactor with asyncio.gather()
    for artifact_revision_id in input.artifact_revision_ids:
        action_result = await info.context.processors.artifact_revision.cleanup.wait_for_complete(
            CleanupArtifactRevisionAction(
                artifact_revision_id=uuid.UUID(artifact_revision_id),
            )
        )
        cleaned_artifact_revisions.append(ArtifactRevision.from_dataclass(action_result.result))

    edges = [
        ArtifactRevisionEdge(node=revision, cursor=to_global_id(ArtifactRevisionEdge, revision.id))
        for revision in cleaned_artifact_revisions
    ]

    artifacts_connection = ArtifactRevisionConnection(
        count=len(cleaned_artifact_revisions),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return CleanupArtifactRevisionsPayload(artifact_revisions=artifacts_connection)


@strawberry.mutation(description="Added in 25.15.0")
async def delete_artifacts(
    input: DeleteArtifactsInput, info: Info[StrawberryGQLContext]
) -> DeleteArtifactsPayload:
    action_result = await info.context.processors.artifact.delete_artifacts.wait_for_complete(
        DeleteArtifactsAction(
            artifact_ids=[uuid.UUID(id) for id in input.artifact_ids],
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    artifacts = []
    for item in action_result.artifacts:
        registry_data = await registry_meta_loader.load(item.registry_id)
        source_registry_data = await registry_meta_loader.load(item.source_registry_id)
        artifacts.append(Artifact.from_dataclass(item, registry_data.url, source_registry_data.url))

    return DeleteArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(description="Added in 25.15.0")
async def restore_artifacts(
    input: RestoreArtifactsInput, info: Info[StrawberryGQLContext]
) -> RestoreArtifactsPayload:
    action_result = await info.context.processors.artifact.restore_artifacts.wait_for_complete(
        RestoreArtifactsAction(
            artifact_ids=[uuid.UUID(id) for id in input.artifact_ids],
        )
    )

    registry_meta_loader = DataLoader(
        apartial(ArtifactRegistryMeta.load_by_id, info.context),
    )

    artifacts = []
    for item in action_result.artifacts:
        registry_data = await registry_meta_loader.load(item.registry_id)
        source_registry_data = await registry_meta_loader.load(item.source_registry_id)
        artifacts.append(Artifact.from_dataclass(item, registry_data.url, source_registry_data.url))

    return RestoreArtifactsPayload(artifacts=artifacts)


@strawberry.mutation(description="Added in 25.14.0")
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
        artifact_revision=ArtifactRevision.from_dataclass(action_result.result)
    )


# TODO: Make this available when only having super-admin privileges
@strawberry.mutation(description="Added in 25.14.0")
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


@strawberry.mutation(description="Added in 25.14.0")
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


@strawberry.mutation(description="Added in 25.14.0")
async def scan_artifact_models(
    input: ScanArtifactModelsInput, info: Info[StrawberryGQLContext]
) -> ScanArtifactModelsPayload:
    action_result = await info.context.processors.artifact.retrieve_models.wait_for_complete(
        RetrieveModelsAction(
            models=[m.to_dataclass() for m in input.models], registry_id=input.registry_id
        )
    )

    edges = []
    for data in action_result.result:
        edges.extend([
            ArtifactRevisionEdge(
                node=ArtifactRevision.from_dataclass(revision),
                cursor=to_global_id(ArtifactRevision, revision.id),
            )
            for revision in data.revisions
        ])

    artifacts_connection = ArtifactRevisionConnection(
        count=len(edges),
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )

    return ScanArtifactModelsPayload(artifact_revision=artifacts_connection)


# Subscriptions
@strawberry.subscription(description="Added in 25.14.0")
async def artifact_status_changed(
    input: ArtifactStatusChangedInput,
) -> AsyncGenerator[ArtifactStatusChangedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield ArtifactStatusChangedPayload(artifact=Artifact())


@strawberry.subscription(description="Added in 25.14.0")
async def artifact_import_progress_updated(
    artifact_revision_id: ID,
) -> AsyncGenerator[ArtifactImportProgressUpdatedPayload, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield ArtifactImportProgressUpdatedPayload()
