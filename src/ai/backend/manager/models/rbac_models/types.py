import enum


class PermissionState(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' state is used when the permission is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' state is used when the permission is permanently removed
    DELETED = "deleted"
