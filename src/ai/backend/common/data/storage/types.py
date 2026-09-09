from __future__ import annotations

import enum
from typing import NewType

from pydantic import ConfigDict

from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.common.types import BackendAISchema

# The operator-declared name of a storage volume, which is its configuration section key.
VolumeName = NewType("VolumeName", str)


class VFolderStorageTarget(BackendAISchema):
    """Target for direct import to a specific virtual folder."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vfolder_id: VFolderIDField
    volume_name: str


class NamedStorageTarget(BackendAISchema):
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
