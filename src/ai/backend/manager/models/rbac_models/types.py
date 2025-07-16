import enum


class PermissionStatus(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' status is used when the permission is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the permission is permanently removed
    DELETED = "deleted"
