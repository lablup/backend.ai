from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel


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


class ObjectStorageStatefulData(ArtifactStorageStatefulData):
    """
    Shared object storage data type for common components.
    This is a copy of manager's ObjectStorageData without the to_dto method.
    """

    id: uuid.UUID
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str


class VFSStorageStatefulData(ArtifactStorageStatefulData):
    """
    Shared VFS storage data type for common components.
    This is a copy of manager's VFSStorageData.
    """

    id: uuid.UUID
    name: str
    host: str
    base_path: Path
