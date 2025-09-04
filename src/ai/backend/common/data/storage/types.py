import enum


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    GIT_LFS = "git_lfs"
