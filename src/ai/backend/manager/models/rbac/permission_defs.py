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


class StorageHostPermission(BasePermission):
    CREATE_FOLDER = enum.auto()

    CLONE = VFolderPermission.CLONE
    ASSIGN_PERMISSION_TO_OTHERS = VFolderPermission.ASSIGN_PERMISSION_TO_OTHERS

    READ_ATTRIBUTE = VFolderPermission.READ_ATTRIBUTE
    UPDATE_ATTRIBUTE = VFolderPermission.UPDATE_ATTRIBUTE
    DELETE_VFOLDER = VFolderPermission.DELETE_VFOLDER

    READ_CONTENT = VFolderPermission.READ_CONTENT
    WRITE_CONTENT = VFolderPermission.WRITE_CONTENT
    DELETE_CONTENT = VFolderPermission.DELETE_CONTENT

    MOUNT_RO = VFolderPermission.MOUNT_RO
    MOUNT_RW = VFolderPermission.MOUNT_RW
    MOUNT_WD = VFolderPermission.MOUNT_WD


class AgentPermission(BasePermission):
    READ_RESOURCE_SLOT = enum.auto()
    UPDATE_SCHEDULABLE = enum.auto()

    READ_ATTRIBUTE = enum.auto()  # id, status, region, scaling_group, schedulable etc
    UPDATE_ATTRIBUTE = enum.auto()

    CREATE_COMPUTE_SESSION = enum.auto()
    CREATE_MODEL_SERVICE_SESSION = enum.auto()


class ScalingGroupPermission(BasePermission):
    READ_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()

    READ_AGENT_RESOURCE_SLOT = AgentPermission.READ_RESOURCE_SLOT
    UPDATE_AGENT_SCHEDULABLE = AgentPermission.UPDATE_SCHEDULABLE

    READ_AGENT_ATTRIBUTE = (
        AgentPermission.READ_ATTRIBUTE
    )  # id, status, region, scaling_group, schedulable etc
    UPDATE_AGENT_ATTRIBUTE = AgentPermission.UPDATE_ATTRIBUTE

    CREATE_COMPUTE_SESSION = AgentPermission.CREATE_COMPUTE_SESSION
    CREATE_MODEL_SERVICE_SESSION = AgentPermission.CREATE_MODEL_SERVICE_SESSION
