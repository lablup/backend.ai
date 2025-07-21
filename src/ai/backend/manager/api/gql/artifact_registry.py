from __future__ import annotations

from enum import Enum
from typing import AsyncGenerator, List, Optional

import strawberry


# Scalars
@strawberry.scalar
class HumanReadableNumber:
    """A scalar representing human-readable numbers like '10g', '2t'"""

    pass


@strawberry.scalar
class DateTime:
    """A scalar representing datetime"""

    pass


@strawberry.scalar
class JSONString:
    """A scalar representing JSON string"""

    pass


# Enums
@strawberry.enum
class ArtifactType(Enum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


@strawberry.enum
class ArtifactStatus(Enum):
    AVAILABLE = "AVAILABLE"
    PULLING = "PULLING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    INSTALLING = "INSTALLING"
    INSTALLED = "INSTALLED"
    FAILED = "FAILED"


@strawberry.enum
class Ordering(Enum):
    ASC = "ASC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC = "DESC"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"


# Input Types
@strawberry.input
class StringFilter:
    """String filtering input"""

    pass


@strawberry.input
class ArtifactFilter:
    type: Optional[List[ArtifactType]] = None
    status: Optional[List[ArtifactStatus]] = None
    name: Optional[StringFilter] = None
    registry: Optional[StringFilter] = None
    source: Optional[StringFilter] = None

    AND: Optional["ArtifactFilter"] = None
    OR: Optional["ArtifactFilter"] = None
    NOT: Optional["ArtifactFilter"] = None
    DISTINCT: Optional[bool] = None


@strawberry.input
class ArtifactOrder:
    name: Optional[Ordering] = None
    type: Optional[Ordering] = None
    size: Optional[Ordering] = None
    updated_at: Optional[Ordering] = None
    created_at: Optional[Ordering] = None
    latest_version: Optional[Ordering] = None


@strawberry.input
class PullArtifactInput:
    artifact_id: strawberry.ID
    version: str


@strawberry.input
class InstallArtifactInput:
    artifact_id: strawberry.ID
    version: str


@strawberry.input
class UpdateArtifactInput:
    artifact_id: strawberry.ID
    target_version: str


@strawberry.input
class DeleteArtifactInput:
    artifact_id: strawberry.ID
    version: str
    force_delete: bool = False


# Object Types
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]


@strawberry.type
class SourceInfo:
    name: Optional[str]
    url: Optional[str]


@strawberry.type
class Artifact:
    name: str
    type: ArtifactType
    status: ArtifactStatus
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    size: HumanReadableNumber
    created_at: DateTime
    updated_at: DateTime
    version: str


@strawberry.type
class ArtifactEdge:
    node: Artifact
    cursor: str


@strawberry.type
class ArtifactConnection:
    edges: List[ArtifactEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class ArtifactGroup:
    id: strawberry.ID
    name: str
    type: ArtifactType
    status: ArtifactStatus
    description: Optional[str]

    @strawberry.field
    def artifacts(
        self, filter: Optional[ArtifactFilter] = None, order: Optional[ArtifactOrder] = None
    ) -> ArtifactConnection:
        # Mock implementation - return empty connection
        return ArtifactConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
            total_count=0,
        )


@strawberry.type
class DownloadProgress:
    artifact_id: strawberry.ID
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
    order: Optional[ArtifactOrder] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
) -> ArtifactConnection:
    # Mock implementation - return empty connection
    return ArtifactConnection(
        edges=[],
        page_info=PageInfo(
            has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
        ),
        total_count=0,
    )


@strawberry.field
def artifact_groups(
    filter: Optional[ArtifactFilter] = None, order: Optional[ArtifactOrder] = None
) -> List[ArtifactGroup]:
    # Mock implementation - return empty list
    return []


@strawberry.field
def artifact(id: strawberry.ID) -> Optional[Artifact]:
    # Mock implementation
    return None


@strawberry.field
def artifact_group(id: strawberry.ID) -> Optional[ArtifactGroup]:
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
def verify_artifact(
    artifact_id: strawberry.ID, version: Optional[str] = None
) -> VerifyArtifactPayload:
    # Mock implementation
    return VerifyArtifactPayload()


@strawberry.mutation
def cancel_pull(artifact_id: strawberry.ID) -> CancelPullPayload:
    # Mock implementation
    return CancelPullPayload()


# Subscriptions
@strawberry.subscription
async def artifact_status_changed(
    artifact_id: Optional[strawberry.ID] = None,
) -> AsyncGenerator[Artifact, None]:
    # Mock implementation
    # In real implementation, this would yield artifacts when status changes
    if False:  # Placeholder to make this a generator
        yield Artifact()


@strawberry.subscription
async def download_progress(artifact_id: strawberry.ID) -> AsyncGenerator[DownloadProgress, None]:
    # Mock implementation
    # In real implementation, this would yield progress updates
    if False:  # Placeholder to make this a generator
        yield DownloadProgress()
