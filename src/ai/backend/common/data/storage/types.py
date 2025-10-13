from __future__ import annotations

import enum


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS = "vfs"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.StrEnum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"
