from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import AsyncGenerator, Optional

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import ByteSize, OrderDirection, StringFilter


# Enums
@strawberry.enum
class ArtifactType(StrEnum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


@strawberry.enum
class ArtifactStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PULLING = "PULLING"
    VERIFYING = "VERIFYING"
    FAILED = "FAILED"


@strawberry.enum
class ArtifactOrderField(StrEnum):
    ID = "ID"
    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    LATEST_VERSION = "LATEST_VERSION"


# Input Types
@strawberry.input
class ArtifactFilter:
    type: Optional[list[ArtifactType]] = None
    status: Optional[list[ArtifactStatus]] = None
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
class ImportArtifactInput:
    artifact_id: ID


@strawberry.input
class UpdateArtifactInput:
    artifact_id: ID


@strawberry.input
class DeleteArtifactInput:
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


ArtifactEdge = Edge[Artifact]


@strawberry.type
class ArtifactConnection(Connection[Artifact]):
    @strawberry.field
    def count(self) -> int:
        # Mock implementation - in real implementation, count from database
        return 0


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
    ) -> ArtifactConnection:
        # Mock implementation - filter artifacts by group type
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


# Mutation Payloads
@strawberry.type
class ImportArtifactPayload:
    artifact: Artifact


@strawberry.type
class UpdateArtifactPayload:
    artifact: Artifact


@strawberry.type
class DeleteArtifactPayload:
    artifact: Artifact


@strawberry.type
class CancelImportArtifactPayload:
    artifact: Artifact


@strawberry.type
class ArtifactStatusChangedPayload:
    artifact_id: ID
    status: ArtifactStatus
    updated_at: datetime


# Query Fields
@strawberry.field
def artifacts(
    filter: Optional[ArtifactFilter] = None,
    order_by: Optional[list[ArtifactOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
) -> ArtifactConnection:
    # Mock implementation - return sample artifacts
    return ArtifactConnection(
        edges=[],
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=None,
            end_cursor=None,
        ),
    )


@strawberry.field
def artifact_groups(
    filter: Optional[ArtifactFilter] = None,
    order_by: Optional[list[ArtifactOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
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
def artifact(id: ID) -> Optional[Artifact]:
    raise NotImplementedError("Artifact retrieval not implemented yet.")


@strawberry.field
def artifact_group(id: ID) -> Optional[ArtifactGroup]:
    raise NotImplementedError("Artifact group retrieval not implemented yet.")


# Mutations
@strawberry.mutation
def import_artifact(input: ImportArtifactInput) -> ImportArtifactPayload:
    raise NotImplementedError()


@strawberry.mutation
def update_artifact(input: UpdateArtifactInput) -> UpdateArtifactPayload:
    raise NotImplementedError()


@strawberry.mutation
def delete_artifact(input: DeleteArtifactInput) -> DeleteArtifactPayload:
    raise NotImplementedError()


@strawberry.mutation
def cancel_import_artifact(artifact_id: ID) -> CancelImportArtifactPayload:
    raise NotImplementedError()


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
