"""User GraphQL enum types."""

from __future__ import annotations

from enum import StrEnum

import strawberry


@strawberry.enum(
    name="UserStatusV2",
    description=(
        "Added in 26.2.0. User account status. "
        "ACTIVE: User can log in and use the system. "
        "INACTIVE: User account is disabled but preserved. "
        "DELETED: User has been soft-deleted. "
        "BEFORE_VERIFICATION: User account is pending email verification."
    ),
)
class UserV2StatusEnumGQL(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"


@strawberry.enum(
    name="UserRoleV2",
    description=(
        "Added in 26.2.0. User role determining access permissions. "
        "USER: Standard user with basic permissions. "
        "ADMIN: Domain administrator with elevated permissions. "
        "SUPERADMIN: System-wide administrator with full access. "
        "MONITOR: Read-only access for monitoring purposes."
    ),
)
class UserV2RoleEnumGQL(StrEnum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    MONITOR = "monitor"
