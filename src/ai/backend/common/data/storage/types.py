from __future__ import annotations

import enum

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
