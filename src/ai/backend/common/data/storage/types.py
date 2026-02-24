from __future__ import annotations

import enum
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.common.types import ArtifactStorageId, ConcreteArtifactStorageId


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


@dataclass(frozen=True)
class ArtifactStorageData:
    """Data class for artifact storage metadata."""

    id: ArtifactStorageId
    name: str
    storage_id: ConcreteArtifactStorageId
    type: ArtifactStorageType


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"
