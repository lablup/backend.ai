import enum


class VFolderPermissionDTO(enum.StrEnum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"
