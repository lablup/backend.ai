"""
Common DTOs for artifact system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CancelImportTaskRequest,
    CleanupRevisionsRequest,
    ImportArtifactsOptions,
    ImportArtifactsRequest,
    UpdateArtifactRequest,
)
from .response import (
    ApproveRevisionResponse,
    ArtifactDTO,
    ArtifactRevisionDTO,
    ArtifactRevisionImportTaskDTO,
    CancelImportTaskResponse,
    CleanupRevisionsResponse,
    GetRevisionDownloadProgressResponse,
    GetRevisionReadmeResponse,
    GetRevisionVerificationResultResponse,
    ImportArtifactsResponse,
    RejectRevisionResponse,
    UpdateArtifactResponse,
)

__all__ = (
    # Request DTOs
    "ImportArtifactsOptions",
    "ImportArtifactsRequest",
    "UpdateArtifactRequest",
    "CleanupRevisionsRequest",
    "CancelImportTaskRequest",
    # Response DTOs - Data
    "ArtifactRevisionDTO",
    "ArtifactDTO",
    "ArtifactRevisionImportTaskDTO",
    # Response DTOs - Responses
    "ImportArtifactsResponse",
    "UpdateArtifactResponse",
    "CleanupRevisionsResponse",
    "ApproveRevisionResponse",
    "RejectRevisionResponse",
    "CancelImportTaskResponse",
    "GetRevisionReadmeResponse",
    "GetRevisionVerificationResultResponse",
    "GetRevisionDownloadProgressResponse",
)
