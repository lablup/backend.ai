from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, Field

from pydantic import BaseModel, ConfigDict

from ai.backend.common.type_adapters import VFolderIDField


class VFolderStorageTarget(BaseModel):
    """Target for direct import to a specific virtual folder."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vfolder_id: VFolderIDField
    volume_name: str


class NamedStorageTarget(BaseModel):
    """Target for named storage lookup via storage pool."""

    storage_name: str


ArtifactStorageTarget = NamedStorageTarget | VFolderStorageTarget


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS_STORAGE = "vfs_storage"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"


class ArtifactStorageStatefulData(BaseModel):
    """Base class for artifact storage stateful data."""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Create instance from dictionary with Pydantic validation."""
        return cls.model_validate(data)

    def to_dict(self) -> Mapping[str, Any]:
        """Convert instance to dictionary with JSON-compatible types."""
        return self.model_dump(mode="json")


class _CommonArtifactStorageStatefulData(ArtifactStorageStatefulData):
    """Common fields for all artifact storage stateful data types."""

    id: uuid.UUID = Field(
        description="Primary key from the artifact_storages table representing the storage configuration",
    )
    name: str = Field(
        description="Human-readable name of the storage used for display and identification purposes",
    )
    host: str = Field(
        description="Hostname or IP address of the server providing the storage backend",
    )


class ObjectStorageStatefulData(_CommonArtifactStorageStatefulData):
    """
    Shared object storage data type for common components.
    This is a copy of manager's ObjectStorageData without the to_dto method.
    """

    access_key: str = Field(
        description="Access key credential used for authenticating API requests to the object storage service",
    )
    secret_key: str = Field(
        description="Secret key credential used for signing and authenticating API requests to the object storage service",
    )
    endpoint: str = Field(
        description="Full endpoint URL of the S3-compatible object storage service (e.g., https://s3.amazonaws.com)",
    )
    region: str = Field(
        description="AWS region or region identifier for the object storage service (e.g., us-east-1, ap-northeast-2)",
    )


class VFSStorageStatefulData(_CommonArtifactStorageStatefulData):
    """
    Shared VFS storage data type for common components.
    This is a copy of manager's VFSStorageData.
    """

    base_path: Path = Field(
        description="Base filesystem path where artifacts are stored in the VFS (e.g., /mnt/vfs/artifacts)",
    )
