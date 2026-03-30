"""
Artifact Registry DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.artifact_registry.request import (
    ArtifactFilterInput,
    ArtifactOrderingInput,
    BackwardPaginationInput,
    DelegateeTargetInput,
    DelegateImportArtifactsInput,
    DelegateScanArtifactsInput,
    ForwardPaginationInput,
    ImportArtifactsOptionsInput,
    OffsetPaginationInput,
    PaginationInput,
    ScanArtifactModelsInput,
    ScanArtifactsInput,
    SearchArtifactsInput,
)
from ai.backend.common.dto.manager.v2.artifact_registry.response import (
    ArtifactNode,
    ArtifactRevisionDataNode,
    ArtifactRevisionImportTaskInfo,
    ArtifactRevisionNode,
    ArtifactWithRevisionsNode,
    DelegateImportArtifactsPayload,
    DelegateScanArtifactsPayload,
    RetrieveArtifactModelPayload,
    ScanArtifactModelsPayload,
    ScanArtifactsPayload,
    SearchArtifactsPayload,
)
from ai.backend.common.dto.manager.v2.artifact_registry.types import (
    ArtifactOrderingField,
    ArtifactRegistryType,
    ArtifactRevisionReadmeInfo,
    OrderDirection,
)

__all__ = (
    # Types
    "ArtifactOrderingField",
    "ArtifactRegistryType",
    "ArtifactRevisionReadmeInfo",
    "OrderDirection",
    # Input models (request)
    "ArtifactFilterInput",
    "ArtifactOrderingInput",
    "BackwardPaginationInput",
    "DelegateImportArtifactsInput",
    "DelegateScanArtifactsInput",
    "DelegateeTargetInput",
    "ForwardPaginationInput",
    "ImportArtifactsOptionsInput",
    "OffsetPaginationInput",
    "PaginationInput",
    "ScanArtifactModelsInput",
    "ScanArtifactsInput",
    "SearchArtifactsInput",
    # Node and Payload models (response)
    "ArtifactNode",
    "ArtifactRevisionDataNode",
    "ArtifactRevisionImportTaskInfo",
    "ArtifactRevisionNode",
    "ArtifactWithRevisionsNode",
    "DelegateImportArtifactsPayload",
    "DelegateScanArtifactsPayload",
    "RetrieveArtifactModelPayload",
    "ScanArtifactModelsPayload",
    "ScanArtifactsPayload",
    "SearchArtifactsPayload",
)
