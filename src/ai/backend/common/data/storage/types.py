import enum


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS = "vfs"
    GIT_LFS = "git_lfs"
