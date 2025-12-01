from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS_STORAGE = "vfs_storage"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"


class ArtifactStorageStatefulData(ABC, BaseModel):
    """Abstract base class for artifact storage stateful data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from dictionary with appropriate type conversions."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert instance to dictionary with appropriate type conversions."""
        raise NotImplementedError


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from dictionary with Pydantic validation."""
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert instance to dictionary with JSON-compatible types."""
        return self.model_dump(mode="json")


class VFSStorageStatefulData(ArtifactStorageStatefulData):
    """
    Shared VFS storage data type for common components.
    This is a copy of manager's VFSStorageData.
    """

    id: uuid.UUID
    name: str
    host: str
    base_path: Path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from dictionary with Pydantic validation."""
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert instance to dictionary with JSON-compatible types."""
        return self.model_dump(mode="json")
