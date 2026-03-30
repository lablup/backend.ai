"""
Common DTOs for artifact registry system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    ArtifactFilterInput,
    ArtifactOrderingInput,
    BackwardPaginationInput,
    DelegateeTargetInput,
    DelegateImportArtifactsRequest,
    DelegateScanArtifactsRequest,
    ForwardPaginationInput,
    ImportArtifactsOptionsInput,
    OffsetPaginationInput,
    PaginationInput,
    ScanArtifactModelsRequest,
    ScanArtifactsRequest,
    SearchArtifactsRequest,
)
from .response import (
    ArtifactDTO,
    ArtifactRevisionDataDTO,
    ArtifactRevisionDTO,
    ArtifactRevisionImportTaskDTO,
    ArtifactRevisionReadmeDTO,
    ArtifactWithRevisionsDTO,
    DelegateImportArtifactsResponse,
    DelegateScanArtifactsResponse,
    RetrieveArtifactModelResponse,
    ScanArtifactModelsResponse,
    ScanArtifactsResponse,
    SearchArtifactsResponse,
)

__all__ = (
    # Request - Nested types
    "DelegateeTargetInput",
    "ImportArtifactsOptionsInput",
    "PaginationInput",
    "ForwardPaginationInput",
    "BackwardPaginationInput",
    "OffsetPaginationInput",
    "ArtifactOrderingInput",
    "ArtifactFilterInput",
    # Request models
    "ScanArtifactsRequest",
    "DelegateScanArtifactsRequest",
    "DelegateImportArtifactsRequest",
    "SearchArtifactsRequest",
    "ScanArtifactModelsRequest",
    # Response - DTOs
    "ArtifactRevisionDTO",
    "ArtifactDTO",
    "ArtifactRevisionDataDTO",
    "ArtifactWithRevisionsDTO",
    "ArtifactRevisionImportTaskDTO",
    "ArtifactRevisionReadmeDTO",
    # Response models
    "ScanArtifactsResponse",
    "DelegateScanArtifactsResponse",
    "DelegateImportArtifactsResponse",
    "SearchArtifactsResponse",
    "ScanArtifactModelsResponse",
    "RetrieveArtifactModelResponse",
)
