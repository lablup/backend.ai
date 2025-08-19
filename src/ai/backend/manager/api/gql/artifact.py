from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import AsyncGenerator, Optional, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.api.gql.base import ByteSize, OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactStatus, ArtifactType
from ai.backend.manager.repositories.artifact.repository import (
    ArtifactFilterOptions,
    ArtifactOrderingField,
    ArtifactOrderingOptions,
    BackwardPaginationOptions,
    ForwardPaginationOptions,
    OffsetBasedPaginationOptions,
)
from ai.backend.manager.services.artifact.actions.authorize import AuthorizeArtifactAction
from ai.backend.manager.services.artifact.actions.cancel_import import CancelImportAction
from ai.backend.manager.services.artifact.actions.delete import DeleteArtifactAction
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact.actions.import_ import ImportArtifactAction
from ai.backend.manager.services.artifact.actions.list import ListArtifactsAction
from ai.backend.manager.services.artifact.actions.scan import ScanArtifactsAction
from ai.backend.manager.services.artifact.actions.unauthorize import UnauthorizeArtifactAction


# TODO: Add more fields
@strawberry.enum
class ArtifactGroupOrderField(StrEnum):
    NAME = "NAME"


@strawberry.input
class ArtifactGroupOrderBy:
    field: ArtifactGroupOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.input
class ArtifactGroupFilter:
    name: Optional[StringFilter] = None

    AND: Optional["ArtifactGroupFilter"] = None
    OR: Optional["ArtifactGroupFilter"] = None
    NOT: Optional["ArtifactGroupFilter"] = None
    DISTINCT: Optional[bool] = None


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
    status: Optional[ArtifactStatus] = None
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
class ImportArtifactsInput:
    artifact_ids: list[ID]
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
    status: ArtifactStatus
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    size: ByteSize
    created_at: datetime
    updated_at: datetime
    version: str
    authorized: bool

    @classmethod
    def from_dataclass(cls, data: ArtifactData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            status=data.status,
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


@strawberry.type
class ArtifactConnection(Connection[Artifact]):
    _total_count: int = 0

    @strawberry.field
    def count(self) -> int:
        return self._total_count

    def set_total_count(self, count: int) -> None:
        self._total_count = count


@strawberry.type
class ArtifactGroup(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    status: ArtifactStatus
    description: Optional[str]

    @strawberry.field
    def artifacts(
        self,
        filter: Optional[ArtifactFilter] = None,
        order_by: Optional[list[ArtifactOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ArtifactConnection:
        all_mock_artifacts: list = []

        # Filter artifacts to match the group's type
        filtered_artifacts = [
            (artifact, cursor)
            for artifact, cursor in all_mock_artifacts
            if artifact.type == self.type
        ]

        edges = [
            ArtifactEdge(node=artifact, cursor=cursor) for artifact, cursor in filtered_artifacts
        ]

        return ArtifactConnection(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


ArtifactGroupEdge = Edge[ArtifactGroup]


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
class CancelImportArtifactPayload:
    artifact_id: ID


@strawberry.type
class ArtifactStatusChangedPayload:
    artifact_id: ID
    status: ArtifactStatus
    updated_at: datetime


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
    # Build filter options
    filters = ArtifactFilterOptions()
    if filter:
        if filter.type:
            filters.artifact_type = filter.type[0] if filter.type else None
        if filter.status:
            filters.status = filter.status
        if filter.name and filter.name.i_contains:
            filters.name_filter = filter.name.i_contains

    # Build ordering options
    ordering = ArtifactOrderingOptions()
    if order_by and order_by[0]:
        order_field_map = {
            ArtifactOrderField.ID: ArtifactOrderingField.CREATED_AT,
            ArtifactOrderField.NAME: ArtifactOrderingField.NAME,
            ArtifactOrderField.TYPE: ArtifactOrderingField.TYPE,
            ArtifactOrderField.SIZE: ArtifactOrderingField.SIZE,
            ArtifactOrderField.CREATED_AT: ArtifactOrderingField.CREATED_AT,
            ArtifactOrderField.UPDATED_AT: ArtifactOrderingField.UPDATED_AT,
        }
        ordering.order_by = order_field_map.get(order_by[0].field, ArtifactOrderingField.CREATED_AT)
        ordering.order_desc = order_by[0].direction == OrderDirection.DESC

    # Choose pagination mode
    if offset is not None or limit is not None:
        # Standard pagination
        pagination = OffsetBasedPaginationOptions(offset=offset, limit=limit)
        forward = None
        backward = None
    else:
        # GraphQL connection pagination
        pagination = None
        # Create forward or backward pagination options based on parameters
        forward = None
        backward = None
        if after is not None or first is not None:
            forward = ForwardPaginationOptions(after=after, first=first)
        if before is not None or last is not None:
            backward = BackwardPaginationOptions(before=before, last=last)

    # Use service layer to get artifacts
    action_result = await info.context.processors.artifact.list_artifacts.wait_for_complete(
        ListArtifactsAction(
            pagination=pagination,
            forward=forward,
            backward=backward,
            ordering=ordering,
            filters=filters,
        )
    )

    # Convert to GraphQL artifacts
    artifacts = [Artifact.from_dataclass(artifact) for artifact in action_result.data]

    # Create edges
    edges = [ArtifactEdge(node=artifact, cursor=str(artifact.id)) for artifact in artifacts]

    # Determine pagination info
    has_next_page = False
    has_previous_page = False
    start_cursor = edges[0].cursor if edges else None
    end_cursor = edges[-1].cursor if edges else None

    if forward or backward:
        # For connection pagination (simplified logic)
        if first and len(edges) == first:
            has_next_page = True  # Could be more accurate with additional service call
        if last and len(edges) == last:
            has_previous_page = True  # Could be more accurate with additional service call
    else:
        # For offset/limit pagination
        current_offset = offset or 0
        has_next_page = (current_offset + len(edges)) < action_result.total_count
        has_previous_page = current_offset > 0

    artifact_connection = ArtifactConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
        ),
    )

    # Set the total count
    artifact_connection.set_total_count(action_result.total_count)
    return artifact_connection


@strawberry.field
def artifact_groups(
    filter: Optional[ArtifactGroupFilter] = None,
    order_by: Optional[list[ArtifactGroupOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Connection[ArtifactGroup]:
    # Mock implementation - return empty connection
    return Connection(
        edges=[],
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
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
def artifact_group(id: ID) -> Optional[ArtifactGroup]:
    # Mock implementation
    return None


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

    artifacts = [Artifact.from_dataclass(item) for item in action_result.result]
    return ScanArtifactsPayload(artifacts=artifacts)


# Mutations
@strawberry.mutation
async def import_artifacts(
    input: ImportArtifactsInput, info: Info[StrawberryGQLContext]
) -> ImportArtifactsPayload:
    imported_artifacts = []
    for artifact_id in input.artifact_ids:
        action_result = await info.context.processors.artifact.import_.wait_for_complete(
            ImportArtifactAction(
                artifact_id=uuid.UUID(artifact_id),
                storage_id=uuid.UUID(input.storage_id),
                bucket_name=input.bucket_name,
            )
        )
        imported_artifacts.append(Artifact.from_dataclass(action_result.result))

    edges = [
        ArtifactEdge(node=artifact, cursor=str(i)) for i, artifact in enumerate(imported_artifacts)
    ]

    artifacts_connection = ArtifactConnection(
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


# Subscriptions
@strawberry.subscription
async def artifact_status_changed(
    artifact_id: Optional[ID] = None,
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
