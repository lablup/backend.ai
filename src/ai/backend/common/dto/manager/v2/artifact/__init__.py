"""
Artifact DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.artifact.request import (
    CancelImportTaskInput,
    CleanupRevisionsInput,
    ImportArtifactsInput,
    UpdateArtifactInput,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    ApproveRevisionPayload,
    ArtifactNode,
    ArtifactRevisionImportTaskInfo,
    ArtifactRevisionNode,
    CancelImportTaskPayload,
    CleanupRevisionsPayload,
    GetRevisionDownloadProgressPayload,
    GetRevisionReadmePayload,
    GetRevisionVerificationResultPayload,
    ImportArtifactsPayload,
    RejectRevisionPayload,
    UpdateArtifactPayload,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactOrderField,
    ArtifactRegistryType,
    ArtifactRevisionInfo,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
    CombinedDownloadProgress,
    OrderDirection,
    VerificationStepResult,
)

__all__ = (
    # Types
    "ArtifactAvailability",
    "ArtifactOrderField",
    "ArtifactRegistryType",
    "ArtifactRevisionInfo",
    "ArtifactRevisionOrderField",
    "ArtifactStatus",
    "ArtifactType",
    "CombinedDownloadProgress",
    "OrderDirection",
    "VerificationStepResult",
    # Input models (request)
    "CancelImportTaskInput",
    "CleanupRevisionsInput",
    "ImportArtifactsInput",
    "UpdateArtifactInput",
    # Node and Payload models (response)
    "ArtifactNode",
    "ArtifactRevisionImportTaskInfo",
    "ArtifactRevisionNode",
    "ApproveRevisionPayload",
    "CancelImportTaskPayload",
    "CleanupRevisionsPayload",
    "GetRevisionDownloadProgressPayload",
    "GetRevisionReadmePayload",
    "GetRevisionVerificationResultPayload",
    "ImportArtifactsPayload",
    "RejectRevisionPayload",
    "UpdateArtifactPayload",
)
