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


class ComputeSessionPermission(BasePermission):
    # `create_session` action should be in {Domain, Project, or User} permissions, not here
    READ_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()
    DELETE_SESSION = enum.auto()

    START_APP = enum.auto()
    EXECUTE = enum.auto()
    CONVERT_TO_IMAGE = enum.auto()


class ScalingGroupPermission(BasePermission):
    # super-admin only
    ASSOCIATE_WITH_SCOPES = enum.auto()
    ASSIGN_AGENTS = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()

    # admin only
    READ_ATTRIBUTE = enum.auto()

    # Permission set of bindings and sub-scopes
    AGENT_PERMISSIONS = enum.auto()
    COMPUTE_SESSION_PERMISSIONS = enum.auto()
    INFERENCE_SERVICE_PERMISSIONS = enum.auto()

    STORAGE_HOST_PERMISSIONS = enum.auto()


class AgentPermission(BasePermission):
    READ_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()

    CREATE_COMPUTE_SESSION = enum.auto()
    CREATE_SERVICE = enum.auto()


class DomainPermission(BasePermission):
    # These permissions limit actions taken directly to domains
    READ_ATTRIBUTE = enum.auto()
    READ_SENSITIVE_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()

    CREATE_USER = enum.auto()
    CREATE_PROJECT = enum.auto()


class ProjectPermission(BasePermission):
    # These permissions limit actions taken directly to projects(groups)
    READ_ATTRIBUTE = enum.auto()
    READ_SENSITIVE_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()
    DELETE_PROJECT = enum.auto()

    ASSOCIATE_WITH_USER = enum.auto()


class ImagePermission(BasePermission):
    READ_ATTRIBUTE = enum.auto()
    UPDATE_ATTRIBUTE = enum.auto()
    CREATE_CONTAINER = enum.auto()

    FORGET_IMAGE = enum.auto()
