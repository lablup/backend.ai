import enum


class BasePermission(enum.StrEnum):
    pass


class VFolderPermission(BasePermission):
    # Only owners can do
    CLONE = enum.auto()
    ASSIGN_PERMISSION_TO_OTHERS = enum.auto()  # Invite, share

    # `create_vfolder` action should be in {Domain, Project, or User} permissions, not here
    READ_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()
    DELETE_VFOLDER = enum.auto()

    READ_CONTENT = enum.auto()
    WRITE_CONTENT = enum.auto()
    DELETE_CONTENT = enum.auto()

    MOUNT_RO = enum.auto()
    MOUNT_RW = enum.auto()
    MOUNT_WD = enum.auto()
