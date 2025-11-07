from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


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
        default=0,
        description="Number of files that have been successfully downloaded",
    )
    downloaded_bytes: int = Field(
        default=0,
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
        description="Error message if download failed",
    )


class DownloadProgressData(BaseModel):
    """
    Download progress data including artifact-level and all file-level information.
    """

    artifact_progress: Optional[ArtifactDownloadTrackingData] = Field(
        description="Artifact-level download progress, None if not found",
    )
    file_progress: dict[str, FileDownloadProgressData] = Field(
        description="Dictionary mapping file paths to their download progress",
    )


class ArtifactRevisionDownloadProgress(BaseModel):
    """
    Download progress with artifact revision status.
    Used for both local and remote download progress.
    """

    progress: Optional[DownloadProgressData] = Field(
        description="Download progress data",
    )
    status: str = Field(
        description="Artifact revision status (SCANNED, PULLING, PULLED, etc.)",
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
