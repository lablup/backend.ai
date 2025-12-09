import enum

from ai.backend.common.data.permission import RoleStatus


class PermissionStatus(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' status is used when the permission is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the permission is permanently removed
    DELETED = "deleted"


# Re-export RoleStatus from common for backward compatibility
__all__ = ("PermissionStatus", "RoleStatus")
