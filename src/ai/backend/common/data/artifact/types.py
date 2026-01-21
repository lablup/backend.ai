from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VerifierResult(BaseModel):
    """Result from a single verifier"""

    success: bool
    infected_count: int
    scanned_at: datetime  # Timestamp when verification started
    scan_time: float  # Time taken to complete verification in seconds
    scanned_count: int
    metadata: dict[str, str]  # Additional metadata from verifier
    error: Optional[str] = None  # For when verifier fails with exception


class VerificationStepResult(BaseModel):
    """Verification result containing results from all verifiers"""

    verifiers: dict[str, VerifierResult]


class ArtifactRegistryType(enum.StrEnum):
    HUGGINGFACE = "huggingface"
    RESERVOIR = "reservoir"


class ArtifactDownloadTrackingData(BaseModel):
    """
    Artifact-level download tracking data stored in Redis.
    """

    model_id: str = Field(
        description="Model identifier",
    )
    revision: str = Field(
        description="Model revision",
    )
    start_time: float = Field(
        description="Download start timestamp (Unix time)",
    )
    last_updated: float = Field(
        description="Last update timestamp (Unix time)",
    )
    total_files: int = Field(
        description="Total number of files in the artifact",
    )
    total_bytes: int = Field(
        description="Total bytes to download across all files",
    )
    completed_files: int = Field(
        description="Number of files that have been successfully downloaded",
    )
    downloaded_bytes: int = Field(
        description="Total bytes downloaded so far across all files",
    )


class FileDownloadProgressData(BaseModel):
    """
    File-level download progress data stored in Redis.
    """

    file_path: str = Field(
        description="File path within the model",
    )
    success: bool = Field(
        default=False,
        description="Whether the file download completed successfully",
    )
    current_bytes: int = Field(
        description="Current bytes downloaded for this file",
    )
    total_bytes: int = Field(
        description="Total bytes for this file",
    )
    last_updated: float = Field(
        description="Last update timestamp (Unix time)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description=(
            "Error message if download failed. "
            "Present when success is False and an error occurred during download. "
            "None when success is True or no error information is available."
        ),
    )


class DownloadProgressData(BaseModel):
    """
    Download progress data including artifact-level and all file-level information.
    """

    artifact_progress: Optional[ArtifactDownloadTrackingData] = Field(
        description="Artifact-level download progress, None if not found",
    )
    file_progress: list[FileDownloadProgressData] = Field(
        description="List of file-level download progress",
    )


class ArtifactRevisionDownloadProgress(BaseModel):
    """
    Download progress with artifact revision status.
    Used for both local and remote download progress.
    """

    progress: Optional[DownloadProgressData] = Field(
        description=(
            "Download progress data. "
            "Present when status is PULLING (actively downloading). "
            "None when status is SCANNED (not yet started), PULLED/AVAILABLE (completed and cleaned up), "
            "or when tracking data is not available."
        ),
    )
    status: str = Field(
        description=(
            "Artifact revision status. "
            "SCANNED: Not yet downloaded. "
            "PULLING: Currently downloading (progress should be present). "
            "PULLED/AVAILABLE: Download completed (progress may be cleaned up). "
            "FAILED: Download failed. "
            "UNSCANNED: Remote status unknown"
        ),
    )


class CombinedDownloadProgress(BaseModel):
    """
    Combined local and remote download progress.
    """

    local: ArtifactRevisionDownloadProgress = Field(
        description="Local download progress and status",
    )
    remote: Optional[ArtifactRevisionDownloadProgress] = Field(
        default=None,
        description="Remote download progress and status. None if not RESERVOIR type, required object if RESERVOIR type",
    )
