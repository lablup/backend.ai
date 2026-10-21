import enum

from ai.backend.common.data.permission.types import PermissionStatus

__all__ = ("PermissionStatus", "RoleStatus")


class RoleStatus(enum.StrEnum):
    """Business state of a role. Soft deletion is ``deleted_at``, not a status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
