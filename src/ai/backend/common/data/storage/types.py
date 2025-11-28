from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from pathlib import Path


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS_STORAGE = "vfs_storage"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"


@dataclass
class ObjectStorageStatefulData:
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


@dataclass
class VFSStorageStatefulData:
    """
    Shared VFS storage data type for common components.
    This is a copy of manager's VFSStorageData.
    """

    id: uuid.UUID
    name: str
    host: str
    base_path: Path
