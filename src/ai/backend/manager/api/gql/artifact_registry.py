from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import AsyncGenerator, Optional

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID


# Scalars
@strawberry.scalar
class HumanReadableNumber:
    """A scalar representing human-readable numbers like '10g', '2t'"""

    pass


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
    VERIFIED = "VERIFIED"
    INSTALLING = "INSTALLING"
    INSTALLED = "INSTALLED"
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


@strawberry.enum
class OrderDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


# Input Types
@strawberry.input
class StringFilter:
    """String filtering input"""

    contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None


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
class PullArtifactInput:
    artifact_id: ID
    version: str


@strawberry.input
class InstallArtifactInput:
    artifact_id: ID
    version: str


@strawberry.input
class UpdateArtifactInput:
    artifact_id: ID
    target_version: str


@strawberry.input
class DeleteArtifactInput:
    artifact_id: ID
    version: str
    force_delete: bool = False


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
    size: HumanReadableNumber
    created_at: datetime
    updated_at: datetime
    version: str

    # @classmethod
    # def resolve_node(cls, node_id: ID) -> Optional["Artifact"]:
    #     # Mock implementation - in real implementation, fetch from database
    #     return None


# Use Strawberry's built-in Relay types
ArtifactEdge = Edge[Artifact]


@strawberry.type
class ArtifactConnection(Connection[Artifact]):
    """Connection for Artifact with totalCount"""

    @strawberry.field
    def totalCount(self) -> int:
        # Mock implementation - in real implementation, count from database
        return 0


@strawberry.type
class ArtifactGroup(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    status: ArtifactStatus
    description: Optional[str]

    # @classmethod
    # def resolve_node(cls, node_id: ID) -> Optional["ArtifactGroup"]:
    #     # Mock implementation - in real implementation, fetch from database
    #     return None

    @strawberry.field
    def artifacts(
        self,
        filter: Optional[ArtifactFilter] = None,
        order_by: Optional[list[ArtifactOrderBy]] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
    ) -> ArtifactConnection:
        # Mock implementation - return empty connection
        return ArtifactConnection(
            edges=[],
            page_info=strawberry.relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
        )


@strawberry.type
class DownloadProgress:
    artifact_id: ID
    progress: float
    status: ArtifactStatus


# Mutation Payloads
@strawberry.type
class PullArtifactPayload:
    artifact: Optional[Artifact] = None


@strawberry.type
class InstallArtifactPayload:
    artifact: Optional[Artifact] = None


@strawberry.type
class UpdateArtifactPayload:
    artifact: Optional[Artifact] = None


@strawberry.type
class DeleteArtifactPayload:
    artifact: Optional[Artifact] = None


@strawberry.type
class VerifyArtifactPayload:
    artifact: Optional[Artifact] = None


@strawberry.type
class CancelPullPayload:
    artifact: Optional[Artifact] = None


# Query Fields
@strawberry.field
def artifacts(
    filter: Optional[ArtifactFilter] = None,
    order_by: Optional[list[ArtifactOrderBy]] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
) -> ArtifactConnection:
    # Mock implementation - return empty connection
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
    first: Optional[int] = None,
    after: Optional[str] = None,
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
    # Mock implementation
    return None


@strawberry.field
def artifact_group(id: ID) -> Optional[ArtifactGroup]:
    # Mock implementation
    return None


# Mutations
@strawberry.mutation
def pull_artifact(input: PullArtifactInput) -> PullArtifactPayload:
    # Mock implementation
    return PullArtifactPayload()


@strawberry.mutation
def install_artifact(input: InstallArtifactInput) -> InstallArtifactPayload:
    # Mock implementation
    return InstallArtifactPayload()


@strawberry.mutation
def update_artifact(input: UpdateArtifactInput) -> UpdateArtifactPayload:
    # Mock implementation
    return UpdateArtifactPayload()


@strawberry.mutation
def delete_artifact(input: DeleteArtifactInput) -> DeleteArtifactPayload:
    # Mock implementation
    return DeleteArtifactPayload()


@strawberry.mutation
def verify_artifact(artifact_id: ID, version: Optional[str] = None) -> VerifyArtifactPayload:
    # Mock implementation
    return VerifyArtifactPayload()


@strawberry.mutation
def cancel_pull(artifact_id: ID) -> CancelPullPayload:
    # Mock implementation
    return CancelPullPayload()


# Subscriptions
@strawberry.subscription
async def artifact_status_changed(
    artifact_id: Optional[ID] = None,
) -> AsyncGenerator[Artifact, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield Artifact()


@strawberry.subscription
async def download_progress(artifact_id: ID) -> AsyncGenerator[DownloadProgress, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield DownloadProgress()
