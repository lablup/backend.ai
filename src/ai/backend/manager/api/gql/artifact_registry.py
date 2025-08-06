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


# TODO: After implementing the actual logic, remove these mock objects
# MODEL artifacts
mock_model_artifact_1 = Artifact(
    id="1",
    name="GPT-4 Language Model",
    type=ArtifactType.MODEL,
    status=ArtifactStatus.AVAILABLE,
    description="Large language model for text generation.",
    registry=SourceInfo(name="Model Registry", url="https://model.registry"),
    source=SourceInfo(name="OpenAI Source", url="https://openai.source"),
    size=ByteSize("3221225472"),  # 3 GB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="1.0.0",
)

mock_model_artifact_2 = Artifact(
    id="2",
    name="BERT Classification Model",
    type=ArtifactType.MODEL,
    status=ArtifactStatus.AVAILABLE,
    description="Bidirectional transformer for classification tasks.",
    registry=SourceInfo(name="Model Registry", url="https://model.registry"),
    source=SourceInfo(name="Hugging Face", url="https://huggingface.co"),
    size=ByteSize("1073741824"),  # 1 GB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="2.1.0",
)

mock_model_artifact_3 = Artifact(
    id="3",
    name="ResNet-50 Vision Model",
    type=ArtifactType.MODEL,
    status=ArtifactStatus.PULLING,
    description="Deep residual network for image classification.",
    registry=SourceInfo(name="Model Registry", url="https://model.registry"),
    source=SourceInfo(name="PyTorch Hub", url="https://pytorch.org/hub"),
    size=ByteSize("536870912"),  # 512 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="1.5.0",
)

# IMAGE artifacts
mock_image_artifact_1 = Artifact(
    id="4",
    name="Ubuntu 22.04 Base Image",
    type=ArtifactType.IMAGE,
    status=ArtifactStatus.AVAILABLE,
    description="Official Ubuntu 22.04 LTS container image.",
    registry=SourceInfo(name="Docker Hub", url="https://hub.docker.com"),
    source=SourceInfo(name="Canonical", url="https://canonical.com"),
    size=ByteSize("268435456"),  # 256 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="22.04",
)

mock_image_artifact_2 = Artifact(
    id="5",
    name="Python 3.11 Runtime Image",
    type=ArtifactType.IMAGE,
    status=ArtifactStatus.AVAILABLE,
    description="Python 3.11 runtime environment with common packages.",
    registry=SourceInfo(name="Docker Hub", url="https://hub.docker.com"),
    source=SourceInfo(name="Python Foundation", url="https://python.org"),
    size=ByteSize("805306368"),  # 768 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="3.11.5",
)

mock_image_artifact_3 = Artifact(
    id="6",
    name="CUDA 12.0 Development Image",
    type=ArtifactType.IMAGE,
    status=ArtifactStatus.VERIFYING,
    description="NVIDIA CUDA 12.0 development environment.",
    registry=SourceInfo(name="NVIDIA NGC", url="https://ngc.nvidia.com"),
    source=SourceInfo(name="NVIDIA", url="https://nvidia.com"),
    size=ByteSize("4294967296"),  # 4 GB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="12.0-devel",
)

# PACKAGE artifacts
mock_package_artifact_1 = Artifact(
    id="7",
    name="NumPy Scientific Package",
    type=ArtifactType.PACKAGE,
    status=ArtifactStatus.AVAILABLE,
    description="Fundamental package for scientific computing with Python.",
    registry=SourceInfo(name="PyPI", url="https://pypi.org"),
    source=SourceInfo(name="NumPy Community", url="https://numpy.org"),
    size=ByteSize("15728640"),  # 15 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="1.24.3",
)

mock_package_artifact_2 = Artifact(
    id="8",
    name="TensorFlow ML Package",
    type=ArtifactType.PACKAGE,
    status=ArtifactStatus.AVAILABLE,
    description="Open source machine learning framework.",
    registry=SourceInfo(name="PyPI", url="https://pypi.org"),
    source=SourceInfo(name="Google", url="https://tensorflow.org"),
    size=ByteSize("471859200"),  # 450 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="2.13.0",
)

mock_package_artifact_3 = Artifact(
    id="9",
    name="FastAPI Web Framework",
    type=ArtifactType.PACKAGE,
    status=ArtifactStatus.FAILED,
    description="Modern, fast web framework for building APIs with Python.",
    registry=SourceInfo(name="PyPI", url="https://pypi.org"),
    source=SourceInfo(name="Sebastián Ramírez", url="https://fastapi.tiangolo.com"),
    size=ByteSize("2097152"),  # 2 MB
    created_at=datetime.now(),
    updated_at=datetime.now(),
    version="0.103.1",
)


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
        all_mock_artifacts = [
            (mock_model_artifact_1, "1"),
            (mock_model_artifact_2, "2"),
            (mock_model_artifact_3, "3"),
            (mock_image_artifact_1, "4"),
            (mock_image_artifact_2, "5"),
            (mock_image_artifact_3, "6"),
            (mock_package_artifact_1, "7"),
            (mock_package_artifact_2, "8"),
            (mock_package_artifact_3, "9"),
        ]

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

# TODO: After implementing the actual logic, remove this mock object
mock_artifact_group1 = ArtifactGroup(
    id="4",
    name="Example Artifact Group",
    type=ArtifactType.MODEL,
    status=ArtifactStatus.AVAILABLE,
    description="This is a mock artifact group for demonstration purposes.",
)

mock_artifact_group2 = ArtifactGroup(
    id="5",
    name="Example Artifact Group",
    type=ArtifactType.IMAGE,
    status=ArtifactStatus.AVAILABLE,
    description="This is a mock artifact group for demonstration purposes.",
)

mock_artifact_group3 = ArtifactGroup(
    id="6",
    name="Example Artifact Group",
    type=ArtifactType.PACKAGE,
    status=ArtifactStatus.AVAILABLE,
    description="This is a mock artifact group for demonstration purposes.",
)


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
        edges=[
            ArtifactEdge(node=mock_model_artifact_1, cursor="1"),
            ArtifactEdge(node=mock_image_artifact_1, cursor="4"),
            ArtifactEdge(node=mock_package_artifact_1, cursor="7"),
        ],
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
        edges=[
            ArtifactGroupEdge(node=mock_artifact_group1, cursor="4"),
            ArtifactGroupEdge(node=mock_artifact_group2, cursor="5"),
            ArtifactGroupEdge(node=mock_artifact_group3, cursor="6"),
        ],
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
def import_artifact(input: ImportArtifactInput) -> ImportArtifactPayload:
    # Mock implementation
    return ImportArtifactPayload(artifact=mock_model_artifact_1)


@strawberry.mutation
def update_artifact(input: UpdateArtifactInput) -> UpdateArtifactPayload:
    # Mock implementation
    return UpdateArtifactPayload(artifact=mock_model_artifact_1)


@strawberry.mutation
def delete_artifact(input: DeleteArtifactInput) -> DeleteArtifactPayload:
    # Mock implementation
    return DeleteArtifactPayload(artifact=mock_model_artifact_1)


@strawberry.mutation
def cancel_import_artifact(artifact_id: ID) -> CancelImportArtifactPayload:
    # Mock implementation
    return CancelImportArtifactPayload(artifact=mock_model_artifact_1)


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
